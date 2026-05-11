# HappyMeal 功能路線圖 v2 / v3

- 文件名稱：功能路線圖概覽
- 版本：v1
- 日期：2026-05-09
- 最後更新：2026-05-11
- 狀態：進行中（V2-01、V2-02、V2-04 程式碼完成，V2-03 暫緩）
- 用途：記錄 v1.x 完成後的後續開發方向，作為優先順序決策依據

---

## 1. 文件定位

v1.x（Priority 1–5）已全數完成。本文件接續規劃下一階段，分為兩個大方向：

- **V2：技術深度展示** — 以求職為主要目的，強化 AI 系統設計深度，不依賴數據準確度
- **V3：產品功能擴張** — 待 AI 辨識與營養數值準確度提升後，再擴大產品形態

選擇這個順序的原因：若數據不夠準確，使用者不會每天依賴這個應用；技術面的深化（RAG、多模型、成本監控）反而同時提升了準確度與求職價值，因此優先執行。

---

## 2. V2：技術深度展示

### 優先順序

| 編號 | 主題 | 求職加分 | 技術依賴 | 狀態 |
|------|------|---------|---------|------|
| V2-01 | RAG + pgvector 向量營養查詢 | ★★★ | 需建立知識庫 | ✅ 程式碼完成（待執行腳本） |
| V2-02 | AI 事件追蹤（DB 可追溯 + Token 監控）| ★★★ | 與 V2-01 同步做 | ✅ 程式碼完成 |
| V2-03 | 多模型切換架構 | ★★☆ | 架構已有基礎 | 暫緩 |
| V2-04 | Prompt 版本管理 | ★★☆ | 極低，加 log 欄位 | ✅ 程式碼完成 |
| V2-05 | 圖片前處理（送 API 前壓縮）| ★★☆ | 低，加一個處理步驟 | 待開發 |
| V2-06 | Token / Payload 壓縮 | ★☆☆ | 限縮為重新估算範圍 | 待開發 |

---

### V2-01：RAG + pgvector 向量營養查詢

**開發文件：** [V2-01-RAG-pgvector-向量營養查詢-開發文件-v1.md](./V2-01-RAG-pgvector-%E5%90%91%E9%87%8F%E7%87%9F%E9%A4%8A%E6%9F%A5%E8%A9%A2-%E9%96%8B%E7%99%BC%E6%96%87%E4%BB%B6-v1.md)

**目標：** 把 `nutrition_resolution.py` 的 `official_source` 那一層升級成向量檢索，用衛福部食品營養成分資料庫 embed 後存進 pgvector，讓未知食物也能找到最相近的官方數據。

**現有基礎：**
- `nutrition_catalog.py` 已有精選目錄，可作為種子資料
- `nutrition_resolution.py` 優先級串聯架構清楚，只需替換 `official_source` 那一層的查詢方式
- PostgreSQL 已在 Lightsail 上，只需啟用 pgvector extension

**技術設計重點：**
- 食物名稱 embedding：將 `canonical_food_name` 與同義詞 embed 成向量
- 查詢時取 top-k 相似食物，再比對 confidence threshold 決定是否使用
- 低於 threshold 仍 fallback 到 `fallback_estimate`，`is_estimated: true`

**面試談資：** 「我把官方營養資料建成向量知識庫，用語意相似度查詢取代關鍵字比對，未知食物也能找到最接近的官方數據。」

---

### V2-02：AI 事件追蹤（DB 可追溯 + Token 監控）

**開發文件：** [V2-02-AI事件追蹤-DB可追溯-Token監控-v1.md](./V2-02-AI%E4%BA%8B%E4%BB%B6%E8%BF%BD%E8%B9%A4-DB%E5%8F%AF%E8%BF%BD%E6%BA%AF-Token%E7%9B%A3%E6%8E%A7-v1.md)

**目標：** 把所有 AI 相關事件寫入 DB（`ai_event_log` 表），同時補上 `input_tokens`、`output_tokens` 欄位，讓指標可以用 SQL 大量查詢，不再依賴人工 grep log。

**現有基礎：**
- `recognition_openai.py` 已有完整的 log 結構（`latency_ms`、`outcome` 等）
- OpenAI Response API 的 `response.usage` 含 `input_tokens`、`output_tokens`，目前未記錄
- `analysis_upload.py`、`analysis_confirm.py` 已有 `db: Session`，可直接寫 DB

**核心設計：**
- 新增 `ai_event_log` 表，一張表涵蓋所有 AI 事件（nullable 欄位依事件類型填入）
- Provider 層（`recognition_openai.py`）回傳 metrics dataclass，由上層統一寫 DB
- Log（stdout）保留不動，DB 是額外的可查詢層

**RAG 上線後：** embedding 呼叫的 token 成本也統一寫入同一張表。

**面試談資：** 「我設計了 DB 層的 AI 事件追蹤，所有辨識結果、Provider 錯誤、Token 用量都可以用 SQL 查詢，不需要 grep log，也方便和 Prompt 版本做交叉分析。」

---

### V2-03：多模型切換架構

**目標：** 讓後端能依設定切換不同 AI provider（OpenAI / Anthropic Claude / Google Gemini），不寫死單一 client。

**現有基礎：**
- `recognition_provider.py` 已定義 `ProviderCandidate` 抽象層
- `recognition_openai.py` 是目前唯一的實作
- `config.py` 的 `ai_food_model` 設定已可從環境變數控制

**技術設計重點：**
- 定義 `RecognitionProvider` protocol（`recognize` / `reestimate` 兩個方法）
- `recognition_openai.py` 實作 OpenAI 版本
- 加入 `recognition_claude.py` 或 `recognition_gemini.py`（至少一個）
- `recognition_provider.py` 依 `ai_provider` 設定路由到對應實作

**面試談資：** 「我設計了 provider abstraction，系統可以在不改業務邏輯的情況下切換 LLM，也方便對比不同模型的辨識準確率。」

---

### V2-04：Prompt 版本管理

**目標：** 讓 prompt 的每次修改可追蹤、可量測效果，而不是 hardcode 一個字串了事。

**現有基礎：**
- Prompt 目前是 `OPENAI_RECOGNITION_PROMPT` 和 `OPENAI_REESTIMATE_PROMPT` 兩個常數
- 已有完整的 log 結構，`candidate_count`、`outcome` 都在

**最小做法：**
- 每個 prompt 加一個版本常數（例如 `RECOGNITION_PROMPT_VERSION = "v1"`）
- 在 `openai_recognition` log 事件裡加入 `prompt_version` 欄位
- 之後改 prompt 就升版，log 裡就能對比不同版本的 `candidate_count`、`outcome` 分布

**進階做法（可選）：**
- 將 prompt 從 code 抽出，存進 DB 或設定檔，支援 A/B 路由

**面試談資：** 「我讓 prompt 的每次迭代都有版本標記，可以從 log 指標判斷 prompt 改動是否真的改善了辨識結果。」

---

### V2-05：圖片前處理（送 API 前壓縮）

**目標：** 在送 OpenAI 前對圖片做 resize 和壓縮，減少 input token 消耗，降低每次辨識成本。

**現有基礎：**
- `recognition_openai.py` 的 `get_image_data_url()` 目前直接讀原始圖片
- `config.py` 已有 `analysis_max_upload_bytes`（5MB 上限）

**技術設計重點：**
- 在 `get_image_data_url()` 前插入一個 preprocess 步驟
- 長邊超過 1024px 時縮小（Vision API 的 `high` detail 模式最高效解析度）
- 輸出 JPEG，quality 85，可顯著縮小檔案大小

**面試談資：** 「我知道 Vision API 的 token 成本主要來自圖片解析度，所以在送出前做了前處理，每次呼叫的成本降低了 X%。」

---

### V2-06：Token / Payload 壓縮（限縮範圍）

**目標：** 優化重新估算時送出的 payload 大小，避免把不必要的欄位送進 context。

**現有狀況：**
- `reestimate_analysis()` 目前把 `items_payload` 整個送出（含 `confidence_score`、`portion_unit` 等欄位）
- 對模型而言，只有 `food_name`、`portion_value`、`user_instruction` 才是有意義的輸入

**最小做法：**
- 在送出前 filter 出 prompt 真正需要的欄位，移除模型不使用的欄位
- 這讓 payload 更精簡，也能在 log 裡記錄壓縮前後的 token 差異

**備註：** 若未來做 AI 對話介面（V3），屆時 context 壓縮會有更大的施力點，到時可擴充。

---

## 3. V3：產品功能擴張

等 V2 技術深度項目完成、AI 辨識準確度提升後，再考慮擴大產品形態。

| 編號 | 主題 | 前置條件 |
|------|------|---------|
| V3-01 | 每日飲食累積紀錄 | 數據可信度足夠讓使用者每天記錄 |
| V3-02 | AI 分析對話介面 | 需有累積紀錄作為 context 基礎 |
| V3-03 | 週期飲食 Insight（週報 / 月報）| 需有累積紀錄 |
| V3-04 | PWA（手機安裝到主畫面）| 隨時可做，但不是目前優先 |
| V3-05 | 條碼掃描（包裝食品精確營養）| 技術獨立，可單獨插入 |

### V3-01：每日飲食累積紀錄

每次分析確認後，計入當日飲食總量，讓使用者看到今天吃了多少。  
**需要新增：** `DailyLog` 資料模型、每日累計 API、前端日誌頁面。

### V3-02：AI 分析對話介面

讓使用者用自然語言問「我今天吃夠了嗎」，AI 根據當日紀錄回答。  
**需要新增：** `ChatSession` / `ChatMessage` 資料模型、chat API、前端對話介面。  
**Token 壓縮：** 此時 V2-06 的壓縮策略才有完整施力點。

### V3-03：週期飲食 Insight

每週或每月 AI 彙總分析使用者的飲食模式，主動提出建議。  
**需要新增：** 排程任務（background job）、insight 生成邏輯、推播或站內通知。

### V3-04：PWA（手機安裝體驗）

加入 `manifest.json` 與 Service Worker，讓 Android 和 iOS 使用者可以把 HappyMeal 安裝到主畫面，提供接近 native app 的體驗。  
技術成本低，可在任何階段插入。

### V3-05：條碼掃描

使用手機相機掃描包裝食品條碼，直接查詢衛福部或 Open Food Facts 資料庫取得精確營養數值，繞過 AI 辨識。  
**需要新增：** 條碼解碼（前端）、條碼查詢 API（後端）。

---

## 4. 明確不做（暫緩至 V4 或不列入）

| 項目 | 原因 |
|------|------|
| 社群功能（分享、追蹤）| 超出目前產品定位 |
| 多語系（i18n）| 目前鎖定台灣市場 |
| Redis 快取 | 目前規模不需要 |
| E2E 自動化測試 | 求職優先順序低，非關鍵 |
| 付費方案 | 超出目前產品階段 |
| 完整食物資料庫搜尋 | V3 之後再考慮 |

---

## 5. V2 建議執行順序

1. ✅ **V2-01 RAG + pgvector** — 核心項目，程式碼完成，需執行 import + generate 腳本驗收
2. ✅ **V2-02 AI 事件追蹤** — `ai_event_log` 表 + `record_ai_event()` + ProviderCallResult 指標傳遞，全數完成
3. ✅ **V2-04 Prompt 版本管理** — `RECOGNITION_PROMPT_VERSION`、`REESTIMATE_PROMPT_VERSION` 常數，已寫入 event log
4. **V2-05 圖片前處理** — 下一個目標
5. **V2-03 多模型切換** — 暫緩，有想法再做
6. **V2-06 Payload 壓縮** — 最後做，收尾優化

---

## 6. 相關文件

- 總覽：[../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
- v1.x 最後完成：[Priority5-觀測性與效能基線-v1.md](./Priority5-%E8%A7%80%E6%B8%AC%E6%80%A7%E8%88%87%E6%95%88%E8%83%BD%E5%9F%BA%E7%B7%9A-v1.md)
