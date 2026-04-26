# Priority 5｜觀測性與效能基線 v1

- 文件名稱：Priority 5｜觀測性與效能基線
- 版本：v1
- 日期：2026-04-26
- 狀態：Draft
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

## 4. 工作拆解

### P5-01 analysis latency

### P5-02 provider timeout / error rate

### P5-03 manual fallback rate

### P5-04 correction rate / re-estimation usage

### P5-05 部署後最小驗收指標

---

## 5. 明確不做

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
