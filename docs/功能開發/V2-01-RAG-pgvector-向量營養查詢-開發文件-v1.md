# V2-01｜RAG + pgvector 向量營養查詢開發文件 v1

- 文件名稱：V2-01｜RAG + pgvector 向量營養查詢開發文件
- 文件類型：操作指南 / 開發規格
- 建立時間：2026-05-09 21:49
- 最後更新：2026-05-11（實作完成）
- 版本：v1
- 狀態：✅ 程式碼完成，待執行腳本驗收
- 目標讀者：HappyMeal 後端開發者、面試作品集維護者
- 使用者目標：把現有 `official_source` 從本地策展 catalog 升級為可查詢衛福部食品營養資料的向量檢索層

---

## 快速導覽

1. 主流做法結論
2. HappyMeal 建議方案
3. 系統邊界與不做事項
4. 資料來源與資料整理
5. Embedding 與 pgvector 設計
6. 查詢流程
7. 後端模組拆解
8. Migration 草案
9. 開發任務拆解
10. 驗收條件
11. 參考來源

---

## 1. 主流做法結論

目前較主流、且適合 HappyMeal 的做法是：

1. 使用 PostgreSQL + pgvector 作為向量儲存，不另外引入獨立 vector database。
2. 食品資料先整理成一筆食物一筆 document，而不是把整份資料任意 chunk。
3. 對「樣品名稱、俗名、英文名稱、分類、內容物描述」組成 embedding text，營養數值仍保留為結構化欄位。
4. 全庫使用同一個 embedding model；不同模型產生的 embedding 不混用。
5. 查詢時先取 top-k，再用相似度 threshold 決定是否接受。
6. pgvector 索引以 HNSW 作為優先選項；資料量很小時可以先 exact search，等資料量與 latency 有壓力再加索引。
7. 對營養查詢這種高風險錯配場景，不建議直接把 top-1 當成事實，應保留 fallback 與可追溯 metadata。

對 HappyMeal 來說，這不是典型「文件問答 RAG」，而是「語意相似食物查詢」。因此重點不是把營養資料丟給 LLM 回答，而是用 embedding 找到最接近的官方食物，再用資料庫中的結構化營養欄位計算結果。

---

## 2. HappyMeal 建議方案

### 2.1 建議架構

新增一層 `official_vector_source`，插入現有 `nutrition_resolution.py` 的 `official_source` 判定位置。

建議優先序：

1. `official_vector_source`：pgvector 查詢命中且 similarity 通過門檻
2. `official_source`：保留目前本地策展 catalog，作為小型高信心覆蓋與測試基準
3. `canonical_mapping`
4. `fallback_estimate`
5. `special_guard`

### 2.2 為什麼不是直接取代全部邏輯

目前 `nutrition_resolution.py` 已有穩定的決策順序與 fallback 能力。V2-01 只需要升級「官方資料來源」這一層，不應重寫 confirm 主鏈。

保留現有本地 catalog 的好處：

1. 黑咖啡、白飯、水煮蛋等已驗收案例仍可做回歸基準。
2. pgvector 查詢失敗、embedding API 暫時不可用、或 threshold 不足時，流程仍可完成。
3. 面試展示時可以清楚說明系統有分層 fallback，不是盲信向量搜尋。

---

## 3. 系統邊界與不做事項

本階段要做：

1. 建立官方營養資料 ingestion pipeline。
2. 建立 PostgreSQL table 與 pgvector extension。
3. 產生並保存食品名稱相關 embedding。
4. 在 `nutrition_resolution.py` 中加入向量查詢路徑。
5. 保存命中來源、相似度與官方資料 id，供除錯與面試展示。

本階段不做：

1. 不做完整前端食物搜尋頁。
2. 不把營養資料交給 LLM 生成答案。
3. 不做醫療級營養判斷。
4. 不做大型 observability dashboard。
5. 不一次支援多個 embedding provider。
6. 不把 Open Food Facts 條碼資料混入本階段；條碼查詢留給 V3-05。

---

## 4. 資料來源與資料整理

### 4.1 主要資料來源

建議使用政府開放資料平臺的「食品營養成分資料集」，提供機關為衛生福利部食品藥物管理署。

該資料集欄位包含：

1. 食品分類
2. 資料類別
3. 整合編號
4. 樣品名稱
5. 俗名
6. 樣品英文名稱
7. 內容物描述
8. 分析項
9. 含量單位
10. 每100克含量
11. 每單位含量
12. 每單位重

### 4.2 資料轉換策略

原始資料通常是「一個食物有多個分析項」。HappyMeal 需要轉成「一個食物一列」，至少整理出：

1. `source_food_id`：官方整合編號或可穩定識別的來源 key
2. `food_category`
3. `sample_name`
4. `common_name`
5. `english_name`
6. `description`
7. `kcal_per_100g`
8. `protein_g_per_100g`
9. `fat_g_per_100g`
10. `carb_g_per_100g`
11. `unit_weight_g`
12. `embedding_text`

### 4.3 embedding text 建議格式

建議用穩定模板組合，不要直接把整列 JSON embed。

```text
食品名稱：白飯
俗名：白米飯、飯
英文名稱：Steamed rice
分類：穀物類
內容物描述：熟白米飯
```

原因：

1. 模板穩定，之後重建 embedding 可重現。
2. 讓中文名稱、俗名與英文名稱都能參與語意比對。
3. 營養數值不用放進 embedding text，避免語意查詢被數字噪音干擾。

---

## 5. Embedding 與 pgvector 設計

### 5.1 Embedding model

建議第一版使用 `text-embedding-3-small`。

理由：

1. 成本低，適合整批食品資料建庫。
2. 支援多語語意檢索，符合台灣食品名稱中英混合情境。
3. 預設維度為 1536，pgvector 可支援。

若未來發現中文食物同義詞召回不足，再評估切換 `text-embedding-3-large`。切換時必須重建全庫 embedding，不可混用。

### 5.2 pgvector distance

OpenAI embeddings 已正規化；實作上可使用：

1. cosine distance：`embedding <=> query_embedding`
2. 或 inner product：`embedding <#> query_embedding`

第一版建議使用 cosine distance，因為語意清楚、便於閱讀與 threshold 設定。

相似度可用：

```sql
similarity = 1 - cosine_distance
```

### 5.3 top-k 與 threshold

建議初始值：

1. `top_k = 5`
2. `accept_threshold = 0.82`
3. `review_threshold = 0.75`

判定方式：

| 條件 | 行為 |
|------|------|
| top-1 similarity >= 0.82 | 使用 `official_vector_source` |
| 0.75 <= top-1 similarity < 0.82 | 暫不自動採用，log 為低信心，可 fallback |
| top-1 similarity < 0.75 | fallback 到既有路徑 |

實際 threshold 必須用真實樣本調整，不應把初始值視為永久規則。

### 5.4 Index 建議

第一版資料量若只有數千筆，可以先不加 approximate index，使用 exact nearest neighbor search，驗證結果正確性。

當資料量或延遲增加後，優先加 HNSW：

```sql
CREATE INDEX CONCURRENTLY ix_nutrition_food_vectors_embedding_hnsw
ON nutrition_food_vectors
USING hnsw (embedding vector_cosine_ops);
```

若資料量非常大且記憶體壓力高，再評估 IVFFlat。pgvector 官方說明中，HNSW 通常有較好的 speed-recall tradeoff，但建置較慢且使用較多記憶體。

---

## 6. 查詢流程

### 6.1 Confirm 時流程

```text
AnalysisConfirmItemRequest
  ↓
NutritionResolutionInput
  ↓
resolve_vector_official_source()
  ↓
top-k vector search
  ↓
similarity threshold
  ↓
NutritionSourceCandidate
  ↓
resolve_portion()
  ↓
FoodAnalysisItem
```

### 6.2 查詢文字

查詢時不要只 embed `normalized_food_name`。建議組合：

```text
食品名稱：{food_name}
標準化名稱：{normalized_food_name}
```

若 AI candidate 有補充資訊，未來可再加入：

1. 份量單位
2. 使用者修正文字
3. 辨識上下文

第一版先保持簡單，避免 query text 過度膨脹。

### 6.3 命中後計算

命中官方資料後，仍沿用現有 `resolve_portion()`：

1. 若使用者輸入 `g` / `ml` 等可換算單位，換算成克重。
2. 用官方資料的每 100g 營養值乘上 `resolved_weight_g / 100`。
3. 寫入 `nutrition_source = "official_vector_source"`。
4. `is_estimated = false`。

如果官方資料有 `每單位重`，可在後續版本用於 `pcs`、`serving` 等單位換算。

---

## 7. 後端模組拆解

建議新增或調整：

| 檔案 | 責任 |
|------|------|
| `app/services/nutrition_vector_ingest.py` | 讀取官方資料、整理成 canonical records |
| `app/services/nutrition_embeddings.py` | 呼叫 embedding API、處理 retry 與成本 log |
| `app/services/nutrition_vector_search.py` | 執行 pgvector top-k 查詢 |
| `app/services/nutrition_resolution.py` | 接入 `resolve_vector_official_source()` |
| `app/core/config.py` | 新增 embedding model、threshold、top-k 設定 |
| `app/db/models.py` | 新增 official nutrition vector table |
| `alembic/versions/*` | 啟用 pgvector 與建立資料表 |

---

## 8. Migration 草案

### 8.1 Extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 8.2 Table

建議第一版 table：

```sql
CREATE TABLE nutrition_food_vectors (
    id VARCHAR(36) PRIMARY KEY,
    source_food_id VARCHAR(100) NOT NULL,
    source_dataset VARCHAR(100) NOT NULL,
    source_version VARCHAR(50) NULL,
    food_category VARCHAR(255) NULL,
    sample_name VARCHAR(255) NOT NULL,
    common_name TEXT NULL,
    english_name VARCHAR(255) NULL,
    description TEXT NULL,
    embedding_text TEXT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    embedding vector(1536) NOT NULL,
    kcal_per_100g NUMERIC(8, 2) NULL,
    protein_g_per_100g NUMERIC(8, 2) NULL,
    fat_g_per_100g NUMERIC(8, 2) NULL,
    carb_g_per_100g NUMERIC(8, 2) NULL,
    unit_weight_g NUMERIC(8, 2) NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

建議 index：

```sql
CREATE INDEX ix_nutrition_food_vectors_source_food_id
ON nutrition_food_vectors (source_food_id);

CREATE INDEX ix_nutrition_food_vectors_sample_name
ON nutrition_food_vectors (sample_name);
```

HNSW index 等資料匯入後再建立：

```sql
CREATE INDEX CONCURRENTLY ix_nutrition_food_vectors_embedding_hnsw
ON nutrition_food_vectors
USING hnsw (embedding vector_cosine_ops);
```

### 8.3 為什麼不直接放進 `food_analysis_items`

`food_analysis_items` 是使用者分析結果，不適合承載官方知識庫。官方資料應獨立成 lookup table，使用者結果只保存命中後的 metadata。

後續可考慮在 `food_analysis_items` 增加：

1. `nutrition_source_record_id`
2. `nutrition_match_similarity`
3. `nutrition_match_rank`

若暫時不加欄位，也至少要在 log 中保留這些資訊。

---

## 9. 開發任務拆解

### V2-01-01 啟用 pgvector 與資料表 ✅

- Alembic migration：`CREATE EXTENSION IF NOT EXISTS vector`
- 建立 `food_nutrition_embeddings` 表（含 HNSW index）
- 新增 SQLAlchemy `FoodNutritionEmbedding` model（Vector(1536)）
- Docker image 改為 `pgvector/pgvector:pg16`
- 85 tests 全過（SQLite 接受 VECTOR 型別名稱）

### V2-01-02 加入 food_code / food_category / nutrients_json 欄位 ✅

- Alembic migration 新增三欄（JSONB）
- `food_code` 建立 unique index，作為 UPSERT key
- model 更新（JSONB → JSON 確保 SQLite 測試相容）

### V2-01-03 官方資料 import ✅（腳本已完成，待執行）

- `backend/scripts/import_nutrition_xlsx.py`
- 讀取衛福部 2025 版 Excel（2503 筆），row 2 為 header，row 3 起為資料
- embedding_text 格式：`{食品分類} {樣品名稱} {俗名1} {俗名2}...`
- canonical_food_name = food_code（確保唯一性）
- nutrients_json 存全部 110 欄
- UPSERT on food_code（idempotent）
- **待執行：**
  ```powershell
  uv run python scripts/import_nutrition_xlsx.py --xlsx "../docs/食品營養成分資料庫2025版UPDATE1EXCEL(另開新視窗).xlsx"
  ```

### V2-01-04 Embedding pipeline ✅（腳本已完成，待執行）

- `backend/scripts/generate_embeddings.py`
- 查詢 embedding IS NULL 的列，每批 100 筆
- 呼叫 `text-embedding-3-small`，向量寫回 DB，每批 commit（斷點重跑安全）
- **待執行：**
  ```powershell
  uv run python scripts/generate_embeddings.py
  ```

### V2-01-05 RAG 接入 nutrition resolution ✅

- 新建 `backend/app/services/rag_lookup.py`
  - `embed_food_query(text)` → 呼叫 OpenAI embeddings
  - `lookup_rag_food(food_name, normalized_food_name, db)` → cosine distance 查詢
  - 任何 exception 靜默 return None（SQLite 測試自動走 fallback）
- 修改 `nutrition_resolution.py`：`resolve_official_source / select_nutrition_source / resolve_item_nutrition` 加 `db: Session | None = None`，RAG 在 keyword catalog 之前
- 修改 `analysis_confirm.py`：`build_analysis_item(payload, db)` 傳入 db
- 實作細節：
  - source label：`"rag_official"`（區別舊的 `"official_source"`）
  - cosine distance threshold：`0.20`（≈ similarity 0.80）
  - 向量傳入：`CAST(:vec AS vector)`，JSON array 格式
  - RAG 命中 → `NutritionPreset(weight_g=100, kcal=per_100g_value, ...)`
- 85 tests 全過

### V2-01-06 驗收與調參（待執行）

1. 確認 2503 筆資料匯入（embedding IS NOT NULL）
2. 送出 `白米飯`、`水煮蛋`、`黑咖啡` → 確認 `nutrition_source = "rag_official"`
3. 送出亂造食物 → 確認退回 fallback
4. 依實測結果調整 threshold（目前 0.20）

---

## 10. 驗收條件

### 10.1 功能驗收

1. PostgreSQL 可成功啟用 pgvector extension。
2. 官方食品資料可匯入 `nutrition_food_vectors`。
3. 每筆資料都有同一 model 產生的 embedding。
4. 查詢 `白飯`、`水煮蛋`、`黑咖啡` 時可命中合理官方資料。
5. 查詢未知食物且 similarity 不足時，不會誤用官方資料，而是 fallback。
6. `confirm_analysis` 對外 response shape 不破壞。

### 10.2 品質驗收

1. 至少 20 筆人工測試樣本中，明顯錯配率低於 10%。
2. `official_vector_source` 命中的 item 必須 `is_estimated = false`。
3. fallback item 仍維持 `is_estimated = true`。
4. log 可看出 top-k、similarity、threshold 與最後採用來源。
5. embedding API 失敗時，不阻斷 confirm 主流程。

### 10.3 面試展示驗收

可以清楚展示：

1. 為什麼選 PostgreSQL + pgvector。
2. 為什麼營養數值保留結構化欄位，而不是讓 LLM 生成。
3. 如何用 threshold 與 fallback 降低錯配風險。
4. 如何用 log 與測試樣本調整 retrieval 品質。

---

## 11. 參考來源

1. pgvector GitHub README：說明 pgvector 支援 exact / approximate nearest neighbor search、HNSW、IVFFlat、cosine distance、filtering、hybrid search 與效能調校。  
   https://github.com/pgvector/pgvector
2. Supabase Semantic Search 文件：說明 semantic search、pgvector table、distance operator、match function 與 index tuning。  
   https://supabase.com/docs/guides/ai/semantic-search
3. Supabase Vector Indexes 文件：建議 pgvector 通常優先使用 HNSW，並列出 distance operator 與維度限制。  
   https://supabase.com/docs/guides/ai/vector-indexes
4. OpenAI Embeddings Guide：說明 embedding 用於 search、clustering、recommendations，`text-embedding-3-small` 預設 1536 維、`text-embedding-3-large` 預設 3072 維，並支援 dimensions 參數。  
   https://platform.openai.com/docs/guides/embeddings
5. OpenAI Embeddings FAQ：說明建議使用 cosine similarity，且 OpenAI embeddings 已正規化。  
   https://help.openai.com/en/articles/6824809-embeddings-frequently-asked-questions
6. 政府資料開放平臺「食品營養成分資料集」：衛生福利部食品藥物管理署提供，含食品分類、樣品名稱、俗名、分析項、每100克含量等欄位。  
   https://data.gov.tw/dataset/8543

---

## 12. 相關文件

1. Roadmap 總覽：[Roadmap-v2-v3-概覽.md](./Roadmap-v2-v3-%E6%A6%82%E8%A6%BD.md)
2. Priority 3 正式營養資料來源：[Priority3-正式營養資料來源與估算策略-v1.md](./Priority3-%E6%AD%A3%E5%BC%8F%E7%87%9F%E9%A4%8A%E8%B3%87%E6%96%99%E4%BE%86%E6%BA%90%E8%88%87%E4%BC%B0%E7%AE%97%E7%AD%96%E7%95%A5-v1.md)
3. Priority 5 觀測性基線：[Priority5-觀測性與效能基線-v1.md](./Priority5-%E8%A7%80%E6%B8%AC%E6%80%A7%E8%88%87%E6%95%88%E8%83%BD%E5%9F%BA%E7%B7%9A-v1.md)
