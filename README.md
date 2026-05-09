# HappyMeal

針對台灣市場的餐點分析應用。使用者拍攝餐點照片，由 AI 辨識食物候選清單與份量估算，使用者確認或修正後，系統計算營養素並給出個人化飲食建議與運動推薦。

**部署：** AWS Lightsail Container Service　**登入：** LINE OAuth 2.0

---

## 技術選型

| 層級 | 技術 |
|---|---|
| 後端 | FastAPI（Python）、SQLAlchemy、Alembic |
| 資料庫 | PostgreSQL（psycopg3）|
| 前端 | React + TypeScript（Vite）|
| AI | OpenAI Responses API（Vision）|
| 驗證 | LINE OAuth 2.0 + 伺服器端 session |
| 部署 | Docker Compose → AWS Lightsail Container Service |
| CI/CD | GitHub Actions |

---

## AI 系統設計

核心是兩階段流程：視覺辨識食物候選，再透過分層策略解析營養數值。

### 第一階段 — 食物辨識（Vision API）

`backend/app/services/recognition_openai.py`

- 將 base64 編碼的餐點圖片送入 OpenAI，設定 `temperature=0`、`max_output_tokens=400`
- Prompt 強制要求固定 JSON schema，模型不能自由發揮；只接受帶有型別欄位的 `candidates[]` 清單
- Response 逐欄解析並做數值夾限（`confidence_score` → `[0, 1]`、`portion_default` → 正數）；格式不合的項目直接丟棄，不往下游傳

**Structured Output Prompt 合約：**
```json
{
  "candidates": [
    {
      "food_name": "顯示名稱",
      "normalized_food_name": "snake_case_英文名",
      "confidence_score": 0.0–1.0,
      "portion_default": 正數,
      "portion_unit": "bowl | plate | cup | pcs | ..."
    }
  ]
}
```

**候選審查流程**（`backend/app/services/analysis_recognition.py`）：

| 結果 | 條件 | `manual_review_required` |
|---|---|---|
| `success` | 至少一個候選的 `confidence_score ≥ 0.6` | `false` |
| `partial` | 有候選但全部低於門檻 | `true` |
| `complete_failure` | Provider 錯誤或回傳空清單 | 視情況 |

低信心候選仍會浮出讓使用者審查，而非靜默丟棄。使用者可修改名稱、調整份量或觸發重新估算。

**錯誤處理** — 每種 Provider 例外對應一個結構化的 `reason` 標籤，直接寫入 JSON log：

| 例外 | `reason` | 使用者訊息方向 |
|---|---|---|
| `RateLimitError` | `quota_exceeded` | 額度不足，請稍後再試 |
| `BadRequestError` | `invalid_image` | 圖片品質問題，請重拍 |
| `APITimeoutError` | `provider_timeout` | 逾時，請重試 |
| `APIConnectionError` | `provider_unavailable` | 連線失敗，請重試 |

### 第一階段 b — 重新估算（Re-estimation）

使用者可提供自然語言修正指令（例如「其實只吃半份」、「是豬肉不是雞肉」），系統將目前候選清單加上使用者指令一起送入第二次 API 呼叫。Prompt 將 `user_instruction` 設為高優先校正 context，避免模型重新發明使用者已修正的項目。

### 第二階段 — 營養解析

`backend/app/services/nutrition_resolution.py`

營養數值透過優先級串聯解析，而非單一查詢：

```
official_source → canonical_mapping → fallback_estimate
       ↓（特殊守衛）
  包裝飲料 → drink_fallback
```

1. **`official_source`** — 精選目錄，含逐項巨量營養素（衛生福利部食品營養成分資料）
2. **`canonical_mapping`** — 關鍵字 / 別名正規化到已知食物 key，再查 preset
3. **`fallback_estimate`** — 找不到對應時使用 `generic_mixed_meal` 估算值

每個解析結果都帶有：
- `nutrition_source` — 使用哪一層來源
- `is_estimated: true` — 若為估算值而非官方數據
- `is_anomalous` — 在回應層計算（不存入 DB），用於標示異常項目

資料來源可追溯至項目層級。前端可顯示「估算值」警示，不需耦合後端的內部來源邏輯。

---

## 可觀測性

結構化 JSON log 輸出至 stdout，從 AWS Lightsail 容器日誌讀取。所有事件透過 request-scoped context 注入帶有 `request_id`、`path`、`user_id`。

| Log 事件 | 關鍵欄位 |
|---|---|
| `openai_recognition` | `outcome`、`reason`、`candidate_count`、`latency_ms` |
| `openai_reestimate` | `outcome`、`reason`、`candidate_count`、`latency_ms` |
| `recognition_result` | `outcome`、`candidate_count`、`manual_review_required` |
| `analysis_upload` | `outcome`、`latency_ms` |
| `analysis_confirm` | `outcome`、`item_count`、`edited_item_count`、`latency_ms` |
| `reestimate_result` | `outcome`、`has_instruction`、`used_fallback`、`latency_ms` |

部署後驗收基線：上傳延遲 < 20s、confirm 延遲 < 1s、Provider 錯誤率 < 10%、人工審查觸發率 < 30%。

---

## 架構決策說明

**為什麼現在不做 RAG / 向量資料庫？**  
目前的營養解析管線刻意選用精選目錄與關鍵字比對，而非 embedding 檢索。這個做法是確定性的、可完整稽核的，且沒有檢索延遲。`is_estimated` 旗標已能向使用者揭示不確定性。待目錄 coverage 成為瓶頸時，RAG 是合理的下一步。

**為什麼 `temperature=0`？**  
營養數值是事實性資料，任何隨機性都會破壞下游 JSON 解析。確定性採樣也讓 Prompt 迭代可測試——同一張圖應產生相同候選。

**為什麼用 session cookie 而不是 JWT？**  
LINE OAuth 回傳短效 token，應用只需要伺服器核發的 session 來追蹤已驗證使用者。伺服器端 session 可即時撤銷，也避免在目前規模下處理 token refresh 的複雜度。

**為什麼儲存 `recommendation_snapshot` 而不是即時計算？**  
建議依賴使用者的 profile（體重、目標、活動量），而使用者之後可能修改。在 confirm 時快照，確保歷史紀錄顯示的是使用者當下實際收到的建議，而非用今天的 profile 重算的版本。

---

## 本地開發

**前置條件：** Docker Desktop、repo 根目錄的 `.env`（需設定 `DATABASE_URL`、`LINE_CHANNEL_ID`、`LINE_CHANNEL_SECRET`、`LINE_CALLBACK_URL`、`SESSION_SECRET_KEY`、`AI_API_KEY`）。

```bash
# 完整 stack，含 hot reload
docker compose -f docker-compose.yml -f docker-compose.override.yml up

# 僅前端（Vite dev server → http://localhost:5173）
cd frontend && npm run dev

# 後端測試（in-memory SQLite，不需要 Postgres）
cd backend
uv run pytest -v
```

---

## 專案結構

```
backend/
  app/
    api/routes/           # FastAPI 路由（analyses、auth、profile、consents）
    services/
      recognition_openai.py   # OpenAI Vision API 整合
      analysis_recognition.py # 候選審查流程
      nutrition_resolution.py # 營養來源優先級串聯
      food_mapping.py         # 正規食物名稱解析
      portion_resolution.py   # 單位換算（碗→g、ml 等）
      analysis_confirm.py     # 確認流程 + 建議快照
    db/models.py          # 所有 SQLAlchemy ORM 模型
    core/
      logging_filters.py  # JSON formatter + request context 注入
  logging.json            # uvicorn 結構化日誌設定
frontend/
  src/
    App.tsx   # 所有頁面與狀態機（約 2500 行）
    api.ts    # 每個 endpoint 的型別化 fetch wrapper
```
