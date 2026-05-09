# Priority 5｜觀測性與效能基線 v1

- 文件名稱：Priority 5｜觀測性與效能基線
- 版本：v1
- 日期：2026-04-26
- 最後更新：2026-05-09
- 狀態：P5-01～P5-05 全數完成
- 用途：為真實 AI provider 與部署後驗收建立最小量測基線

---

## 1. 文件定位

本文件處理的是 PRD v1 gap-closing plan 中的 Priority 5。

它的目標不是做完整監控平台，而是讓後續調整 provider、prompt 與部署品質時，有基本數據可判讀。

---

## 2. 目標

至少能回答：

1. analysis 平均多久
2. provider timeout 多不多
3. 失敗率高不高
4. 使用者多常落入 manual fallback
5. candidate correction 與 re-estimation 使用情況如何

---

## 3. 目前狀態

目前可視為已知進度如下：

1. 專案已有基本 logging 結構與 request context / filter 能力，可作為後續觀測性擴充基礎
2. 部署、CI/CD 與本地 Docker 主鏈已經建立，具備開始補最小量測的條件
3. AI provider 錯誤型態已在實際除錯中暴露出 quota、bad request、timeout 類需求，方向已經明確

目前仍未完成的重點：

1. analysis latency、provider error rate、manual fallback rate 等指標仍未形成固定紀錄機制
2. candidate correction rate 與 re-estimation usage 仍未有可追蹤欄位或事件設計
3. 目前仍較依賴人工看 log 與手動排錯，尚未形成最小驗收儀表或系統化觀測流程

---

## 4. 工作拆解與完成紀錄

### P5-01 Analysis Latency ✅

已完成（2026-05-09）：
- `upload_analysis_image()`、`confirm_analysis()`、`reestimate_analysis()` 三個主要入口各加入端到端 `latency_ms` 量測
- log event：`analysis_upload`、`analysis_confirm`、`reestimate_result`

### P5-02 Provider Timeout / Error Rate ✅

已完成（2026-05-09）：
- `recognition_openai.py` 所有 except block 補入 `latency_ms`（含失敗路徑）
- reestimate 路徑補齊缺少的 `BadRequestError` handler

### P5-03 Manual Fallback Rate ✅

已完成（2026-05-09）：
- 發現並修正 `JsonFormatter._optional_fields` 遺漏所有 analysis 欄位的問題（P5-01/02 的 log 欄位原本不會輸出）
- `recognition_result` 四個路徑統一補入 `candidate_count` 與 `manual_review_required`
- 新增欄位：`latency_ms`、`candidate_count`、`item_count`、`has_instruction`、`used_fallback`、`manual_review_required`

### P5-04 Correction Rate / Re-estimation Usage ✅

已完成（2026-05-09）：
- `is_user_edited` 從 `AnalysisReestimateItemRequest` 上移至父類 `AnalysisConfirmItemRequest`（向後相容）
- confirm log 補入 `edited_item_count`
- `_optional_fields` 補入 `edited_item_count`

### P5-05 部署後最小驗收指標 ✅

已完成（2026-05-09）：
- 部署至 AWS Lightsail 後，從 Container service → Logs tab 人工查看 stdout JSON log
- 確認 `openai_recognition`：`latency_ms` 5300ms、`candidate_count` 3、`outcome: "success"`
- 確認 `recognition_result`：`outcome: "success"`、`manual_review_required: false`
- 確認 `analysis_upload`：`latency_ms` 5487ms
- 確認 `analysis_confirm`：`latency_ms` 53ms、`item_count` 3、`edited_item_count` 0
- 全部五項指標均正常流入，驗收通過

---

## 5. P5-05 部署後最小驗收 Checklist

部署完成後，人工執行下列查詢確認量測正常運作。

**查詢方式：** AWS Lightsail Console → Container service → Logs tab，直接閱讀容器 stdout 的 JSON log 輸出。

**不需要查詢 PostgreSQL**：P5 所有指標均來自 application log，不寫入資料庫。

---

### 5-1 Analysis Latency（P5-01）

查詢條件：`event = "analysis_upload"` 或 `"analysis_confirm"`

確認項目：
- `latency_ms` 欄位存在且為數字
- `analysis_upload` 正常應在 5,000–20,000 ms（含 AI 辨識）
- `analysis_confirm` 正常應在 200–1,000 ms（純 DB 寫入）

---

### 5-2 Provider Error Rate（P5-02）

查詢條件：`event = "openai_recognition"` 或 `"openai_reestimate"`

確認項目：
- 成功事件：`outcome = "success"`，含 `latency_ms` 與 `candidate_count`
- 失敗事件：`outcome = "failure"`，含 `reason`（`quota_exceeded` / `provider_timeout` / `invalid_image` / `provider_unavailable`）與 `latency_ms`
- 初期可接受失敗率 < 10%；`provider_timeout` 比例偏高時評估是否調整 timeout 設定

---

### 5-3 Manual Fallback Rate（P5-03）

查詢條件：`event = "recognition_result"`

確認項目：
- 所有事件均含 `outcome`、`candidate_count`、`manual_review_required`
- `manual_review_required = true` 事件（`partial` + `complete_failure`）佔比即為 fallback rate
- 初期預期 fallback rate < 30%；持續偏高需回頭檢查 prompt 或圖片品質

---

### 5-4 Correction Rate / Re-estimation Usage（P5-04）

**Re-estimation：** 查詢條件 `event = "reestimate_result"`

確認項目：
- `outcome`、`candidate_count`、`has_instruction`、`used_fallback`、`latency_ms` 均存在
- `has_instruction = true` 比例反映使用者主動補充說明的頻率

**Correction Rate：** 查詢條件 `event = "analysis_confirm"`

確認項目：
- `edited_item_count` 欄位存在（前端尚未傳 `is_user_edited` 前值為 0，待前端補上後才有意義）
- `item_count` 反映每次分析的食物數量

---

### 5-5 整體驗收結論

| 指標 | log event | 關鍵欄位 | 初期可接受基線 |
|------|-----------|---------|--------------|
| Upload latency | `analysis_upload` | `latency_ms` | < 20,000 ms |
| Confirm latency | `analysis_confirm` | `latency_ms` | < 1,000 ms |
| Provider error rate | `openai_recognition` | `outcome`, `reason` | < 10% |
| Manual fallback rate | `recognition_result` | `manual_review_required` | < 30% |
| Re-estimation usage | `reestimate_result` | `outcome`, `has_instruction` | 觀察期，無強制基線 |
| Correction rate | `analysis_confirm` | `edited_item_count` | 待前端補上後再設基線 |

---

## 6. 明確不做

1. 完整 observability platform 建設
2. 大規模 dashboard 專案
3. 與商業報表綁定的指標擴張

---

## 6. 驗收條件

1. 至少有最小指標可供人工判讀
2. provider 問題能透過紀錄快速分辨是 timeout、bad request 還是 quota 問題
3. 能判斷 candidate review 是否真的降低了流程中斷

---

## 7. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. 用量與部署估算： [../部署與用量預估-v1.md](../%E9%83%A8%E7%BD%B2%E8%88%87%E7%94%A8%E9%87%8F%E9%A0%90%E4%BC%B0-v1.md)
