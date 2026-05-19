# Redis Cache 設計說明：RAG Lookup 快取層

建立時間：2026-05-19 09:00

---

## 快速導覽

- [一、背景：為什麼 RAG Lookup 需要 Cache](#一背景為什麼-rag-lookup-需要-cache)
- [二、Cache 層在整體流程中的位置](#二cache-層在整體流程中的位置)
- [三、Cache Key 設計](#三cache-key-設計)
- [四、命中與未命中流程](#四命中與未命中流程)
- [五、快取「查無」結果（Null Cache）](#五快取查無結果null-cache)
- [六、降級設計（Graceful Degradation）](#六降級設計graceful-degradation)
- [七、快取失效策略](#七快取失效策略)
- [八、異動檔案總覽](#八異動檔案總覽)

---

## 一、背景：為什麼 RAG Lookup 需要 Cache

### 目前確認分析的流程

使用者在前端按下「確認」後，後端對每一個食物項目都會依序執行以下動作：

```
使用者確認（含 N 個食物項目）
  └─ 每個項目各自執行：
       └─ 決定營養來源
            └─ 嘗試向量查詢（RAG Lookup）
                 ├─ ① 呼叫 OpenAI Embeddings API（取得食物向量）
                 └─ ② 對資料庫執行 pgvector cosine 相似度查詢
```

### 兩個操作的代價

**① OpenAI Embeddings API**

將「白米飯 white_rice」這段文字送到 OpenAI，換回一組 1,536 個數字組成的向量（浮點數陣列），用來代表這個食物的語意位置。

- 每次呼叫約需 200–500 毫秒（受網路影響）
- 有 API 使用費用（雖然 text-embedding-3-small 很便宜，但累積可觀）
- **關鍵特性：相同的文字輸入，永遠回傳完全相同的向量**

**② pgvector cosine 查詢**

拿到向量後，對整張 `food_nutrition_embeddings` 資料表做相似度掃描，找出最接近的官方食物記錄。

- 每次查詢約需 50–200 毫秒（隨資料筆數增長）
- **關鍵特性：相同的向量輸入，永遠找到相同的最近鄰記錄**

### 重複計算的問題

台灣日常飲食的食物種類有限，「白米飯」、「雞腿便當」、「炒青菜」這類食物每天都有大量使用者查詢。

目前的設計下：

- 使用者 A 確認「白米飯」→ 呼叫一次 OpenAI、查一次 pgvector
- 使用者 B 確認「白米飯」→ 再呼叫一次 OpenAI、再查一次 pgvector
- 同一使用者先預估後確認 → 又各呼叫一次 OpenAI、查一次 pgvector

這些計算的**輸入完全相同、輸出也完全相同**，卻每次都重新執行，是明確的浪費。

---

## 二、Cache 層在整體流程中的位置

Cache 層插入在「決定向量」之前，作為第一道查詢關卡：

```
使用者確認（含 N 個食物項目）
  └─ 每個項目各自執行：
       └─ 決定營養來源
            └─ 嘗試向量查詢（RAG Lookup）
                 │
                 ▼
            ┌─────────────┐
            │  查詢 Redis  │  ← 新增的快取層（約 10ms）
            └──────┬──────┘
                   │
          ┌────────┴────────┐
          │ 命中（Hit）      │ 未命中（Miss）
          │                 │
          ▼                 ▼
       直接回傳        ① OpenAI Embeddings API
       快取結果        ② pgvector cosine 查詢
                       ③ 將結果寫入 Redis
                       ④ 回傳結果
```

**重要原則：Cache 層不改變任何現有邏輯。**

- Cache 命中時：完全跳過 OpenAI 和 pgvector，直接回傳快取的營養資料
- Cache 未命中時：執行原有的完整流程，結果寫入 Redis 後再回傳
- Cache 故障時：靜默忽略，直接走原有流程（詳見第六節）

---

## 三、Cache Key 設計

### Key 的組成

```
rag:v1:{食物文字的 sha256 前 16 碼}

範例：
  食物文字："白米飯 white_rice"
  sha256  ："a3f8c2d1e4b7..."（取前 16 碼）
  完整 Key："rag:v1:a3f8c2d1e4b7..."
```

### 為什麼不用 user_id 作為 Key 的一部分

一般 Web 應用的 Cache 通常需要帶上 user_id，因為同一資源對不同使用者有不同的值。

但 RAG Lookup 的特性相反——「白米飯」的向量查詢結果對任何使用者都完全一樣，因此 Cache Key 只需要代表「食物是什麼」，不需要代表「誰在查」。

這讓 Cache 能夠**跨使用者共用**，大幅提升命中率。

### 為什麼使用 sha256 雜湊

食物名稱可能包含中文字、空格或特殊字元，直接作為 Redis Key 可能遇到編碼問題或長度限制。將文字雜湊後得到固定長度的十六進位字串，可以確保 Key 的格式永遠一致且安全。

### 版本前綴（`v1`）的作用

版本前綴是快取失效策略的核心設計，詳見第七節。

---

## 四、命中與未命中流程

### Cache 命中（Hit）

```
收到食物：「白米飯 white_rice」
  │
  ▼
產生 Cache Key："rag:v1:a3f8c2d1..."
  │
  ▼
向 Redis 查詢
  │
  ▼
找到快取資料（JSON 格式的營養數值）
  │
  ▼
直接組裝成 FoodNutritionEmbedding 物件
  │
  ▼
回傳給呼叫方（跳過 OpenAI 與 pgvector）

耗時：約 10–15 ms
```

### Cache 未命中（Miss）

```
收到食物：「蒜炒山蘇」（罕見食物，尚未快取）
  │
  ▼
產生 Cache Key："rag:v1:f9a2b3c4..."
  │
  ▼
向 Redis 查詢 → 查無資料
  │
  ▼
呼叫 OpenAI Embeddings API（~300ms）
→ 取得 1,536 維向量
  │
  ▼
對 food_nutrition_embeddings 執行 pgvector 查詢（~100ms）
→ 找到最近鄰記錄（或確認查無符合）
  │
  ▼
將結果序列化後存入 Redis（TTL = 7 天）
  │
  ▼
回傳結果

耗時：約 400–600 ms（與現在相同）
```

Cache 未命中只發生在「這個食物第一次被任何使用者查詢」時，之後所有使用者查詢同樣食物都走命中路徑。

---

## 五、快取「查無」結果（Null Cache）

### 問題

pgvector 查詢可能因為 cosine distance 超過閾值（0.20）而回傳「查無符合」，此時 `lookup_rag_food()` 回傳 `None`，系統退回到關鍵字目錄查詢。

如果不快取這個「查無」的結果，下次同樣的食物進來時仍然會重複呼叫 OpenAI 和 pgvector，只是為了得到相同的「查無」答案。

### 解法

將「查無」也作為有效的快取結果存入 Redis，以 `null` 值（JSON 的 null）表示。

```
Redis 中的值   →   代表的意義
─────────────────────────────────────────────
{...JSON...}   →   有找到，這是營養資料
null           →   查過了，但沒有符合的記錄
（key 不存在）  →   從未查詢過
```

這樣系統就能清楚區分「還沒查過」和「查過但沒有」，避免對查不到的食物重複浪費呼叫次數。

---

## 六、降級設計（Graceful Degradation）

### 核心原則

Redis 是效能輔助層，不是功能必要條件。Redis 不可用時，系統應自動退回原有流程，使用者完全感知不到異常。

### 降級觸發的情況

- Redis 服務本身無法連線（網路問題、服務重啟）
- Redis 操作超時
- Redis 回傳非預期格式的資料

### 降級行為

```
任何 Redis 操作發生例外
  │
  ▼
靜默捕捉例外（不拋出、不 log error）
  │
  ▼
以 debug 等級記錄例外訊息（供排查使用）
  │
  ▼
直接執行原有的 OpenAI + pgvector 流程
  │
  ▼
正常回傳結果（使用者不受影響）
```

這個設計確保了加入 Redis 後，**系統的可靠性下限不低於加入前**。

---

## 七、快取失效策略

### TTL 設定

每一筆 Cache 的存活時間設為 **7 天（604,800 秒）**。

設定依據：
- `food_nutrition_embeddings` 資料表的更新頻率極低，只有手動執行 `generate_embeddings.py` 時才會變動
- 食物的官方營養數值（衛福部資料）幾乎不會變動
- 7 天後自然過期，下次查詢時重新取得最新結果

### 主動失效：版本號機制

當 `food_nutrition_embeddings` 資料更新後，若希望所有快取立即失效，不需要逐一刪除 Redis 中的每一筆 Key，只需將程式碼中的版本號從 `v1` 改為 `v2`：

```
舊 Key："rag:v1:a3f8c2d1..."  ← 不會再被查詢，7 天後自動消失
新 Key："rag:v2:a3f8c2d1..."  ← 第一次查詢時重新建立
```

這個方式稱為「Key 版本遷移」（Key Versioning），是管理大量快取失效最簡單且安全的做法。**不需要執行 FLUSHALL 或 DEL 指令**，避免誤刪其他資料。

### 何時需要升版本號

| 情境 | 是否需要升版本 |
|---|---|
| 執行了 `generate_embeddings.py` 重新建立向量 | ✅ 需要 |
| 修改了 `COSINE_DISTANCE_THRESHOLD` 閾值 | ✅ 需要 |
| 修改 Prompt v3 之後重新辨識 | ❌ 不需要（RAG 是確認階段才觸發） |
| Redis 服務重啟 | ❌ 不需要（資料已清空） |
| 日常部署更新 | ❌ 不需要 |

---

## 八、異動檔案總覽

| 檔案 | 異動性質 | 說明 |
|---|---|---|
| `requirements.txt` | 新增套件 | 加入 `redis`（連線函式庫）與 `hiredis`（C 加速解析器） |
| `app/core/config.py` | 新增設定欄位 | 讀取 `REDIS_URL` 環境變數 |
| `app/core/redis_client.py` | 新增檔案 | Redis 連線工廠，含降級回傳 None 的機制 |
| `app/services/rag_lookup.py` | 修改核心邏輯 | 在原有 embed + pgvector 流程前後插入 cache 查詢與寫入 |

**不需要異動的部分：**

- 所有呼叫 `lookup_rag_food()` 的上層服務（`nutrition_resolution.py` 等）介面完全不變
- 資料庫 schema（無 migration）
- 前端程式碼
- 所有現有測試（SQLite 環境不執行 RAG，降級行為維持原樣）
