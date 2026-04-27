# HappyMeal 真實 AI 食物辨識 MVP 規格 v1

## 1. 文件資訊

- 文件名稱：HappyMeal 真實 AI 食物辨識 MVP 規格
- 版本：v1
- 日期：2026-04-22
- 狀態：Draft
- 文件類型：參考文件 Reference + 說明文件 Explanation
- 用途：定義 HappyMeal 第一版真實 AI 食物辨識的產品決策、OpenAI 成本試算邏輯、後端切層、API 規格、錯誤處理、fallback、資料流、驗收標準，以及 Candidate Confirmation 前端 UX 規格。

---

## 2. 文件定位

本文件不取代 [PRD-v1.md](../PRD-v1.md)、[System-Architecture-v1.md](../System-Architecture-v1.md) 與 [IA-User-Flows-v1.md](../IA-User-Flows-v1.md)。

本文件的角色是把「Priority 2｜真實 AI 食物辨識 provider 接入」收斂成可落地的 MVP 規格。

本文件回答的問題是：

1. 第一版真實 AI 食物辨識要做到什麼程度
2. 為什麼目前先選 OpenAI + GPT-5.4 mini，而不是更重的方案
3. 後端服務應如何切層，才能先做單一 provider、又保留後續替換空間
4. 成本應如何估算，而不是只憑模型名稱做感覺式判斷
5. 若辨識不完美，前端如何靠「手動修正非常順」完成主流程

不在本文件範圍內的內容：

1. 完整營養資料來源的最終供應商決策
2. 上線後商業方案與計費策略
3. 多 provider routing、AB testing、queue worker 等第二階段能力
4. 每日累積飲食紀錄或完整食物搜尋資料庫

---

## 3. 本輪決策摘要

### 3.1 產品與使用情境假設

1. 分析目標是「整份餐點中的多個食物」，不是只抓單一主食。
2. 食物場景不預設限縮，但優先以台灣日常生活常見飲食為主。
3. 第一版若能同時支援飲料辨識更好，但不把飲料拆成獨立流程。
4. 可接受 AI 辨識普通，但不能讓主流程卡住；手動修正順暢度比追求單次辨識完美更重要。
5. 使用者可接受第三方雲端 AI provider。

### 3.2 第一版 provider 決策

1. 第一版採單一 provider，不做多 provider 切換。
2. 第一版優先採 OpenAI。
3. 模型首選為 GPT-5.4 mini。
4. 若後續實測成本超出預期，再評估降為 GPT-5.4 nano。
5. 第一版不建議直接使用 GPT-5.4 旗艦模型，因為對 HappyMeal 的成本效益不佳。

### 3.3 為什麼先選 GPT-5.4 mini

1. 比旗艦模型便宜，較適合 MVP 驗證。
2. 相比傳統 vision label API，較能處理台灣日常混合餐、飲料與語意描述。
3. 相比專用 food API，更容易先接上現有主鏈並自定結構化輸出。
4. 現有 PRD 已接受「AI 不準時，由使用者手動修正後完成分析」，但前提仍是 AI 至少提供部分可用候選；若 AI 完全失敗，產品應優先引導重拍或換圖。因此第一版關鍵不是把模型做到最強，而是把 correction flow 做到最低摩擦。

### 3.4 風險提醒

1. 月預算若只有約新台幣 200 元，較適合內部 PoC 或小規模封測，不適合直接開給高活躍真實使用者長期使用。
2. 依 [部署與用量預估-v1.md](../部署與用量預估-v1.md) 的分析量假設，真實外部成本很可能先卡在 AI API，而不是 AWS 本身。
3. 若未來 correction rate 長期偏高，應優先優化 normalization 與 UX，再評估更換 provider。

---

## 4. HappyMeal 的真實 AI 食物辨識 MVP 規格整理成一頁

### 4.1 目標

在不改變 HappyMeal 現有主鏈的前提下，把 mock candidate 替換成真實 AI 食物辨識，並保留手動修正、營養映射與歷史保存流程。

### 4.2 MVP 範圍

1. 輸入：單張餐點照片。
2. 支援：多食物餐盤；飲料若可辨識則一併回傳。
3. 輸出：1 到 5 個候選項目。
4. 每個候選至少包含：顯示名稱、normalized food name 候選、信心分數、份量數值、份量單位、是否為飲料。
5. 候選結果進入前端 Candidate Confirmation 供使用者修改。
6. 使用者修改候選內容或補充備註後，可選擇再次請 AI 協助估算名稱補全、份量與候選調整，但 AI 只提供建議，不直接覆蓋使用者最終確認值。
7. confirm 後仍由營養資料來源計算 kcal、protein、fat、carb，不直接相信 AI 估出的營養數值。

### 4.3 非目標

1. 不保證醫療級或專業營養師等級準確度。
2. 不處理影片、即時串流相機或連拍序列。
3. 不做完整食物資料庫搜尋體驗。
4. 不做多 provider fallback routing。

### 4.4 公開 API 輸入輸出

#### POST /analyses

用途：建立分析草稿。

輸入：無。

輸出：

```json
{
  "id": "analysis_id",
  "status": "draft",
  "analyzed_at": "2026-04-22T12:34:56Z"
}
```

#### POST /analyses/{analysis_id}/image

用途：上傳圖片並取得 AI 候選結果。

輸入：`multipart/form-data`，欄位 `file`。

建議輸出：

```json
{
  "analysis_id": "analysis_id",
  "status": "awaiting_confirmation",
  "recognition_status": "success",
  "message": null,
  "candidates": [
    {
      "food_name": "雞腿便當",
      "normalized_food_name": "braised_chicken_lunch_box",
      "confidence_score": 0.84,
      "portion_default": 1.0,
      "portion_unit": "box",
      "is_beverage": false
    },
    {
      "food_name": "紅茶",
      "normalized_food_name": "black_tea",
      "confidence_score": 0.61,
      "portion_default": 1.0,
      "portion_unit": "cup",
      "is_beverage": true
    }
  ]
}
```

`recognition_status` 建議值：

1. `success`：有足夠候選可直接進入確認。
2. `partial`：有候選，但信心偏低或份量估計不穩，需要前端明顯提醒使用者確認。
3. `complete_failure`：沒有足夠可靠候選，應直接引導使用者重拍或換圖，而不是要求手動補完整份餐點。

補充：目前程式已補出 `recognition_status`，並以 `message`、`fallback_reason` 作為輔助欄位；`partial` 的判定規則仍在後續收斂中，因此目前較穩定的已落地分流是 `success` 與 `complete_failure`。

#### POST /analyses/{analysis_id}/confirm

用途：送出修正後的食物與份量，產生最終營養與建議。

輸入：

```json
{
  "items": [
    {
      "food_name": "雞腿便當",
      "normalized_food_name": "braised_chicken_lunch_box",
      "portion_value": 1.0,
      "portion_unit": "box",
      "confidence_score": 0.84
    },
    {
      "food_name": "紅茶",
      "normalized_food_name": "black_tea",
      "portion_value": 1.0,
      "portion_unit": "cup",
      "confidence_score": 0.61
    }
  ]
}
```

輸出沿用現有分析結果格式，並保留免責聲明。

#### POST /analyses/{analysis_id}/re-estimate

用途：當使用者已在 Candidate Confirmation 修改部分內容後，再次請 AI 協助估算候選與份量。

設計原則：

1. 這不是重新建立 analysis，也不是直接覆蓋使用者輸入。
2. 這是一個「AI 建議刷新」動作，用於幫助使用者減少手動填寫成本。
3. 回傳結果應與目前表單並存，前端可選擇套用部分欄位，而不是強制全量替換。

建議輸入：

```json
{
  "items": [
    {
      "food_name": "雞腿便當",
      "normalized_food_name": "braised_chicken_lunch_box",
      "portion_value": 1.0,
      "portion_unit": "box",
      "confidence_score": 0.84,
      "is_user_edited": true
    },
    {
      "food_name": "紅茶",
      "normalized_food_name": "black_tea",
      "portion_value": 1.0,
      "portion_unit": "cup",
      "confidence_score": 0.61,
      "is_user_edited": false
    }
  ],
  "user_instruction": "我已把主餐改成雞腿便當，請幫我重新看配菜和飲料份量是否合理"
}
```

建議輸出：

```json
{
  "analysis_id": "analysis_id",
  "recognition_status": "partial",
  "message": "AI 已根據你修改後的內容重新估算，請再次確認份量與飲料",
  "candidates": [
    {
      "food_name": "雞腿便當",
      "normalized_food_name": "braised_chicken_lunch_box",
      "confidence_score": 0.88,
      "portion_default": 1.0,
      "portion_unit": "box",
      "is_beverage": false,
      "suggestion_source": "re_estimate"
    },
    {
      "food_name": "紅茶",
      "normalized_food_name": "black_tea",
      "confidence_score": 0.68,
      "portion_default": 0.8,
      "portion_unit": "cup",
      "is_beverage": true,
      "suggestion_source": "re_estimate"
    }
  ]
}
```

### 4.5 錯誤處理與 fallback

#### 上傳前置錯誤

1. 非 JPG / PNG：回 `400 Bad Request`。
2. 超過大小限制：回 `400 Bad Request`。
3. analysis 非 draft：回 `409 Conflict`。

#### AI provider 錯誤

1. provider timeout：不要讓系統卡死；若本次無可靠候選，應回 `complete_failure` 並引導重拍或換圖。
2. provider 5xx 或 network error：記錄錯誤、保留 analysis，前端顯示「辨識暫時失敗，請重拍或稍後再試」。
3. provider 回傳格式不完整：經 normalization 後若仍有部分候選，回 `partial`；若無足夠候選，改為 `complete_failure`。

#### 再次估算錯誤

1. `re-estimate` timeout 或失敗：保留使用者當前已編輯內容，不可清空表單。
2. `re-estimate` 結果與使用者已編輯值衝突時：以前端當前值為主，AI 僅作為建議候選。
3. 若使用者已做大量手動修正，再次估算應顯示柔性提醒，避免使用者誤以為 AI 結果一定比自己新輸入更正確。

#### 營養映射錯誤

1. 候選食物找不到正式 nutrition mapping：在確認頁就要求使用者改名或改選標準化項目，不要等到結果頁才失敗。
2. confirm 時若仍無法映射：回 `400 Bad Request`，並指出是哪一個 item 不支援。

### 4.6 高層資料流

以下流程以現有 API 主鏈為基礎，描述實際請求、後端處理、狀態變化與 fallback 決策點。

#### Phase A 建立分析草稿

1. 前端呼叫 `POST /analyses`。
2. 後端驗證使用者已登入，並完成必要 consent 檢查。
3. 後端建立一筆 `FoodAnalysis`，初始狀態為 `draft`。
4. 後端回傳 `analysis_id`、`status=draft`、`analyzed_at`。
5. 前端進入 Start Analysis，準備拍照或上傳圖片。

#### Phase B 上傳圖片與暫存

1. 前端以 `multipart/form-data` 呼叫 `POST /analyses/{analysis_id}/image`。
2. 路由層把檔案交給 `analysis_upload`。
3. `analysis_upload` 先確認分析單屬於當前使用者，且狀態仍為 `draft`。
4. `analysis_upload` 驗證 MIME type 與檔案大小。
5. 驗證通過後，後端把圖片寫入暫存位置。
6. 此時 analysis 尚未完成，只是進入「可辨識處理」階段。

#### Phase C 呼叫辨識流程

1. `analysis_upload` 呼叫 `analysis_recognition.recognize_analysis_image(...)`。
2. `analysis_recognition` 讀取圖片位元組、MIME type、analysis context。
3. `analysis_recognition` 建立 provider request，內容至少包含：

- 固定 system instruction
- HappyMeal 要求的 JSON schema
- 單張餐點圖像輸入
- 台灣日常飲食、多食物、飲料可辨識、可估份量的任務描述

4. `analysis_recognition` 呼叫 `recognition_openai`。
5. `recognition_openai` 以 GPT-5.4 mini 發送請求，帶入 timeout 與結構化輸出要求。
6. `recognition_openai` 接收 provider response，先轉成 provider-level result，不直接回傳給 API。

#### Phase D 後端正規化與判定

1. `analysis_recognition` 將 provider-level result 交給 `recognition_normalization`。
2. `recognition_normalization` 對每個候選做以下處理：

- 將自由文字 food name 映射成 HappyMeal 可用的 `normalized_food_name`
- 將份量單位統一成系統可支援單位，例如 `box`、`plate`、`bowl`、`cup`、`pcs`
- 檢查 confidence score 是否低於建議門檻
- 檢查候選是否重複、是否過度模糊、是否缺少份量資訊

3. `analysis_recognition` 依 normalization 結果決定 `recognition_status`：

- `success`：至少有足夠候選可直接確認
- `partial`：有候選，但低信心、份量不穩或需要使用者特別確認
- `complete_failure`：沒有足夠可靠候選，應改為引導使用者重拍或換圖

4. `analysis_recognition` 產出對外 `AnalysisCandidateResponse` 需要的標準格式。
5. `analysis_recognition` 同步記錄最小觀測資料，例如 provider latency、candidate count、partial / complete_failure 分布與 warning 數量。

#### Phase E 更新分析狀態並回 Candidate Confirmation

1. `analysis_upload` 收到辨識結果後，若結果為 `success` 或 `partial`，才將 analysis 狀態更新為 `awaiting_confirmation`。
2. 若 `recognition_status=complete_failure`，應保留可重試上下文，但前端不應直接把使用者送進完整人工補填流程。
3. 後端回傳：

- `analysis_id`
- `status`：成功或部分成功時為 `awaiting_confirmation`；完全失敗時為可重試的狀態或等價表達
- `recognition_status`
- `message`
- `candidates`

4. 前端進入 Candidate Confirmation 頁：

- `success`：直接顯示候選卡片
- `partial`：顯示候選卡片並加上柔性提醒
- `complete_failure`：顯示辨識失敗訊息，提供重拍 / 換圖或重新分析動作

5. Candidate Confirmation 應同時保留一個次要動作：`再次請 AI 估算`，供使用者在修改部分內容或補充備註後再次取得建議。

#### Phase F 使用者修正與確認

1. 使用者可在 Candidate Confirmation 完成：

- 修改食物名稱
- 調整份量數值與單位
- 刪除誤判候選
- 補新增食物或飲料
- 在已修改部分內容或補充備註後，再次請 AI 協助估算

2. 前端在送出前做最小驗證：

- 至少保留 1 個 item
- food name 不可空白
- portion value 必須大於 0

3. 若使用者點擊 `再次請 AI 估算`：

- 前端送出當前表單內容至 `POST /analyses/{analysis_id}/re-estimate`
- 後端以原始圖片 + 使用者最新修正內容作為上下文，再請 AI 重新估算
- 前端將回傳結果以「建議更新」方式套用，不直接覆蓋使用者欄位

4. 若使用者已滿意當前內容，前端呼叫 `POST /analyses/{analysis_id}/confirm`。

#### Phase G Confirm、營養映射與結果生成

1. 後端確認 analysis 屬於當前使用者，且狀態為 `awaiting_confirmation`。
2. 後端逐一處理 `items`：

- 驗證欄位完整性
- 用 `normalized_food_name` 查詢 nutrition mapping
- 若單位不相容或查無對應，回 `400 Bad Request`

3. 後端計算每個 item 的營養素與整餐 totals。
4. 後端結合 profile 與 goal，產生 recommendation 與 recommended exercises。
5. 後端保存：

- `FoodAnalysisItem`
- totals
- recommendation snapshot

#### Phase H 清理、保存與回結果頁

1. confirm 成功後，後端刪除暫存原始圖片。
2. analysis 狀態更新為 `completed`。
3. 後端回傳最終分析結果、營養總和、建議、推薦運動與免責聲明。
4. 前端進入 Analysis Result。
5. 歷史列表與 detail 後續只讀取分析摘要，不再依賴原始圖片。

#### Phase I 異常與 fallback 分支

1. 若 provider timeout：

- 記錄 timeout
- 不讓 analysis 卡死在 `draft`
- 回 `complete_failure`，引導使用者重拍或換圖

2. 若 provider 回傳格式錯誤或候選不足：

- 記錄 parsing / normalization error
- 視候選品質回 `partial` 或 `complete_failure`

3. 若使用者確認後 nutrition mapping 仍失敗：

- 在 confirm API 回明確錯誤訊息
- 保留 analysis 於 `awaiting_confirmation`
- 讓使用者回到確認頁修正，而不是重建整筆 analysis

4. 若 `re-estimate` 失敗：

- 保留 Candidate Confirmation 當前表單狀態
- 顯示 `AI 重新估算失敗，你目前的修改已保留，可直接繼續或稍後再試`
- 不應迫使使用者離開確認頁或重新上傳圖片

### 4.7 驗收標準

1. 使用者可從真實圖片取得至少 1 個候選，或在完全失敗時收到清楚的重拍 / 換圖引導。
2. AI 部分成功時，使用者可在不離開主鏈的情況下完成修正與 confirm。
3. 結果頁仍能顯示總熱量、三大營養素、建議與免責聲明。
4. 原始圖片完成流程後仍會刪除。
5. 會記錄 provider latency、timeout、error rate、partial rate 與 complete failure rate。

---

## 5. OpenAI 成本試算表邏輯

### 5.1 目的

成本試算表不是要算出一個永遠正確的固定單價，而是要讓團隊快速回答以下問題：

1. 每月可承受多少分析次數
2. 單次分析的成本上限是多少
3. 哪些變數最影響成本
4. 何時需要從 GPT-5.4 mini 調整到更便宜模型或更低解析度策略

### 5.2 試算表分頁建議

1. `Assumptions`：輸入假設與定價。
2. `Scenario`：不同 DAU / 分析次數 / 圖片策略情境。
3. `Actuals`：上線後實際使用量回填。
4. `Decision`：是否超出預算與建議動作。

### 5.3 Assumptions 欄位建議

| 欄位                                    | 說明                                 | 範例  |
| --------------------------------------- | ------------------------------------ | ----- |
| 月預算 TWD                              | 可接受月上限                         | 200   |
| 匯率 USD/TWD                            | 方便換算                             | 32.5  |
| 月預算 USD                              | `月預算 TWD / 匯率`                  | 6.15  |
| 註冊使用者數                            | 粗估用戶池                           | 100   |
| DAU                                     | 每日活躍人數                         | 10    |
| 每位 DAU 每日分析次數                   | 每人平均分析餐數                     | 2     |
| 每月分析次數                            | `DAU * 每日分析次數 * 30`            | 600   |
| 每次請求文字 input tokens               | system prompt + schema + instruction | 1200  |
| 每次請求圖片 input tokens               | 由平台實測回填                       | 3000  |
| 每次請求 cached input tokens            | 可快取部分，例如固定 system prompt   | 800   |
| 每次請求 output tokens                  | JSON 結果長度                        | 350   |
| GPT-5.4 mini input 單價 USD / 1M        | OpenAI 價格                          | 0.75  |
| GPT-5.4 mini cached input 單價 USD / 1M | OpenAI 價格                          | 0.075 |
| GPT-5.4 mini output 單價 USD / 1M       | OpenAI 價格                          | 4.50  |

### 5.4 單次成本公式

令：

1. `uncached_input_tokens = 文字 input tokens + 圖片 input tokens - cached input tokens`
2. `cached_input_tokens = 可快取 input tokens`
3. `output_tokens = 每次請求 output tokens`

則：

$$
單次成本(USD) = \frac{uncached\_input\_tokens \times 0.75 + cached\_input\_tokens \times 0.075 + output\_tokens \times 4.50}{1,000,000}
$$

> 備註：上式使用 GPT-5.4 mini 目前公開文字 token 單價。圖片實際 token 量需以上線前實測為準，因此試算表應把「圖片 input tokens」視為可調欄位，而不是寫死值。

### 5.5 月成本公式

$$
月成本(USD) = 單次成本(USD) \times 每月分析次數
$$

$$
月成本(TWD) = 月成本(USD) \times 匯率
$$

### 5.6 預算可承受單次成本公式

$$
可承受單次成本(USD) = \frac{月預算(USD)}{每月分析次數}
$$

這個欄位最重要，因為它直接回答「現在這個量級下，每次分析最多能花多少」。

### 5.7 Decision 分頁規則建議

1. 若 `月成本(TWD) <= 月預算 TWD`：標記為 `可接受`。
2. 若 `月成本(TWD)` 落在月預算的 `100% 到 130%`：標記為 `接近上限，需實測後再決定`。
3. 若 `月成本(TWD) > 月預算 TWD * 1.3`：標記為 `超出預算，需降模型或降低每次 token 用量`。

### 5.8 上線後最該回填的實測欄位

1. 每次分析的實際圖片 token 用量
2. 平均 output tokens
3. complete failure rate
4. correction rate
5. 平均 latency 與 p95 latency

### 5.9 預算判讀原則

1. 新台幣 200 元適合 PoC 或少量封測，不適合直接預設為 100 人規模長期月預算。
2. 若實際 correction rate 低且完成率高，可以接受稍高單次成本。
3. 若 correction rate 高、成本也高，優先調整 prompt、輸出長度與圖片策略，再考慮換模型。

---

## 6. 若使用 GPT-5.4 mini，後端服務應如何切層最乾淨

### 6.1 切層原則

1. `routes` 不知道 OpenAI 細節。
2. `analysis_upload` 只做上傳主鏈 orchestration，不直接實作 provider 細節。
3. provider adapter 專門處理 OpenAI 請求與回應。
4. normalization 與 nutrition mapping 為獨立邏輯，不綁定任何 provider。
5. 對外 API 格式由 HappyMeal 自己定義，不直接暴露 provider 原始 JSON。

### 6.2 建議模組切分

#### 現有入口

1. `backend/app/api/routes/analyses.py`
2. `backend/app/services/analysis_upload.py`
3. `backend/app/services/analysis_confirm.py`

#### 建議新增服務

1. `backend/app/services/analysis_recognition.py`
2. `backend/app/services/recognition_provider.py`
3. `backend/app/services/recognition_openai.py`
4. `backend/app/services/recognition_normalization.py`
5. `backend/app/services/nutrition_mapping.py`
6. `backend/app/schemas/recognition.py`

### 6.3 各層責任

#### analysis_upload.py

責任：

1. 驗證圖片格式與大小。
2. 儲存暫存圖片。
3. 呼叫 `analysis_recognition.recognize_analysis_image(...)`。
4. 依辨識結果決定 analysis 是否進入 `awaiting_confirmation`，或保留在可重試的上傳上下文。
5. 回傳對外 `AnalysisCandidateResponse`。

不負責：

1. OpenAI prompt 組裝。
2. provider JSON parsing。
3. 食物名稱 normalization 細節。

#### analysis_recognition.py

責任：

1. 作為辨識流程 application service。
2. 呼叫 provider adapter。
3. 呼叫 normalization service。
4. 產出 HappyMeal 標準候選格式。
5. 決定 `success / partial / complete_failure`。
6. 記錄 latency、partial / complete_failure、warning。

#### recognition_provider.py

責任：

1. 定義 provider interface 或 protocol。
2. 保證未來替換 provider 時，主流程不需大改。

建議介面概念：

```python
class RecognitionProvider(Protocol):
    def recognize_meal_image(self, image_bytes: bytes, mime_type: str) -> ProviderRecognitionResult:
        ...
```

#### recognition_openai.py

責任：

1. 實作 OpenAI API 呼叫。
2. 維護 system prompt、response schema、timeout。
3. 將 provider 原始回應轉為 `ProviderRecognitionResult`。

#### recognition_normalization.py

責任：

1. 把 provider 回傳的自由文字轉成 HappyMeal 可用的 normalized food key。
2. 統一份量單位，例如 `cup`、`box`、`bowl`、`pcs`。
3. 對低信心或模糊結果加 warning。

#### nutrition_mapping.py

責任：

1. 提供 `normalized_food_name -> nutrition data` 對應。
2. 支援 confirm 時的正式資料查詢。
3. 不與 provider 綁死。

### 6.4 建議流程分工圖

1. Router 收到 `/analyses/{id}/image`
2. `analysis_upload` 驗證並存圖
3. `analysis_upload` 呼叫 `analysis_recognition`
4. `analysis_recognition` 呼叫 `recognition_openai`
5. `recognition_openai` 回傳 provider-level result
6. `analysis_recognition` 呼叫 `recognition_normalization`
7. `analysis_recognition` 產出 HappyMeal candidate response
8. `analysis_upload` 更新分析狀態並回 API response

### 6.5 為什麼這樣切最乾淨

1. OpenAI 改 prompt 或換 SDK 時，不會污染 upload service。
2. 日後若從 OpenAI 改成專用 food API，只需換 provider adapter 與少量 normalization 規則。
3. 測試可拆成 upload 測試、provider mock 測試、normalization 測試，不會全部卡在整合測試。
4. 這種切法最符合 HappyMeal 目前「單一 provider，但保留替換空間」的需求。

---

## 7. 「手動修正非常順」拆成前端 Candidate Confirmation 的具體 UX 規格

### 7.1 頁面目標

讓使用者在最短時間內完成以下任務：

1. 看懂這餐被辨識成哪些食物
2. 快速刪掉錯誤項目
3. 快速修改名稱與份量
4. 補上 AI 漏掉的食物或飲料
5. 有信心地進到結果頁

### 7.2 UX 成功指標

1. 多數使用者可在 30 秒內完成常見餐點確認。
2. 不需要返回上一頁或重傳圖片才能修正小錯誤。
3. 若 AI 完全失敗，使用者能快速理解應重拍或換圖；若 AI 部分成功，使用者能在同頁完成少量修正。

### 7.3 畫面結構

由上到下建議順序：

1. 頁首摘要：`幫你先抓到這餐可能的內容，請花幾秒確認。`
2. 圖片縮圖與隱私提醒短句。
3. 候選食物列表。
4. `新增食物` 按鈕。
5. `再次請 AI 估算` 或 `重拍 / 換圖` 次要按鈕。
6. `確認並查看結果` 主要 CTA。

### 7.4 候選卡片規格

每個候選卡片至少包含：

1. 食物名稱欄位。
2. 信心分數標籤。
3. 份量數值輸入。
4. 份量單位選單。
5. `刪除` 動作。
6. 若為飲料，顯示 `飲料` tag。

### 7.5 互動細節

#### 編輯名稱

1. 直接在卡片內編輯，不要開新頁。
2. 預設顯示 AI 建議名稱，但可一鍵進入可編輯狀態。
3. 若未來有標準化名稱搜尋，應在輸入時提供下拉建議。

#### 調整份量

1. 預設帶入 AI 估計值。
2. 常見單位優先，例如 `box`、`plate`、`bowl`、`cup`、`pcs`。
3. 份量加減應可單手操作，建議有 `-` / `+` 快捷鈕。

#### 刪除誤判

1. 每張卡片都要有明確 `刪除`。
2. 刪除後應可 `復原`，避免誤觸造成重填。

#### 補新增食物

1. `新增食物` 為高可見但次要 CTA。
2. 新增後直接生成空白卡片。
3. 空白卡片預設 focus 在食物名稱欄位。

#### 再次請 AI 估算

1. 在 Candidate Confirmation 頁提供次要按鈕 `再次請 AI 估算`。
2. 此動作用途是：當使用者已修正一部分內容，或補充像「我只吃半份」、「這不是甜不辣，是炸雞」這類備註後，請 AI 依據最新表單狀態重新推估其他候選或份量。
3. 重新估算時應保留目前表單內容，不得先清空畫面。
4. 回來的 AI 結果應以「可套用建議」方式呈現，而不是直接覆蓋使用者欄位。
5. 若差異較大，前端可標示 `AI 新建議`，讓使用者決定是否採用。

### 7.6 低信心與失敗情境

#### low confidence

1. `confidence_score < 0.7` 時，卡片顯示柔性提醒，例如 `這項可能需要你多確認一下`。
2. 不要用紅色錯誤感表現，避免增加壓力。

#### complete_failure

1. 若 AI 沒有可靠候選，不應直接把使用者送進完整人工補填頁。
2. 畫面文案改為 `這張照片我這次沒有把握，請重拍或換一張更清楚的圖片。`
3. 提供高可見的 `重拍 / 換圖` 動作，而不是預設建立多張空白食物卡片。
4. 若使用者之後重新上傳並取得部分候選，才進入 Candidate Confirmation 與後續 `再次請 AI 估算` 流程。

### 7.7 CTA 與驗證規則

1. 至少保留 1 個有效 item 才能送出。
2. 食物名稱空白時不可送出。
3. 份量需大於 0。
4. 若單位與標準化食物不相容，應在卡片內即時顯示說明。

### 7.8 手機優先細節

1. 主要 CTA 固定在底部安全區上方。
2. 卡片間距夠大，避免誤觸。
3. 每張卡片預設收納足夠資訊，但不要強迫多層展開。
4. 鍵盤彈出時，當前編輯卡片需自動滾動到可視區。

### 7.9 不要做的事

1. 不要要求使用者回到上一頁重傳，只為了修正一兩個名稱。
2. 不要把信心分數表現成技術性過強的指標說教。
3. 不要把手動輸入藏在低可見度文字連結中。
4. 不要讓新增、刪除、改份量分散到多個頁面。

---

## 8. 觀測性與驗收建議

### 8.1 最小監測指標

1. `analysis_provider_latency_ms`
2. `analysis_provider_timeout_count`
3. `analysis_provider_error_count`
4. `analysis_complete_failure_count`
5. `analysis_correction_submit_count`
6. `analysis_candidate_count_avg`
7. `analysis_reestimate_request_count`
8. `analysis_reestimate_apply_rate`
9. `analysis_reestimate_error_count`

### 8.2 第一版最值得追的產品指標

1. 上傳後進入 Candidate Confirmation 的成功率。
2. Candidate Confirmation 到 Result 的完成率。
3. 每筆分析的平均修正項目數。
4. 每筆分析是否補新增食物。
5. 飲料項目的漏判率。
6. 再次估算功能的使用率與採用率。

### 8.3 驗收問題清單

1. 台灣常見便當、自助餐、早餐店、手搖飲等情境是否至少能部分辨識。
2. AI 失準時，使用者是否仍能完成流程。
3. GPT-5.4 mini 的單次成本是否在可接受範圍。
4. p95 分析時間是否符合 PRD `8` 秒內目標。

---

## 9. 建議後續實作順序

1. 先抽出 recognition provider 邊界與 internal schema。
2. 接入 GPT-5.4 mini，讓 `/analyses/{id}/image` 不再回 mock candidate。
3. 補 recognition status、message 與 complete failure / partial 分流。
4. 補 Candidate Confirmation 的新增、刪除、快速調整份量 UX。
5. 補 `re-estimate` API 與 Candidate Confirmation 的 `再次請 AI 估算` 互動，但要以前端保留使用者當前輸入為前提。
6. 補最小觀測性與成本回填欄位。
7. 真實流量與 correction rate、re-estimation 採用率出來後，再決定是否要換模型或改供應商。

---

## 10. 建議 commit message

`docs(ai): 補上真實食物辨識 MVP 規格與成本試算邏輯`
