# Priority 2｜真實 AI 食物辨識與候選修正 v1

- 文件名稱：Priority 2｜真實 AI 食物辨識與候選修正
- 版本：v1
- 日期：2026-04-30
- 狀態：V1.X 收斂中，P0 辨識分流與 re-estimate 失敗提示已完成
- 用途：把真實 AI 辨識主鏈、candidate confirmation、fallback 與穩定化驗收補成可追蹤的開發主題

---

## 1. 文件定位

本文件處理的是 PRD v1 gap-closing plan 中的 Priority 2。

這是目前最接近 HappyMeal 核心產品價值的主題，也是最容易讓開發方向變得模糊的區塊，因此需要比總覽文件更細的拆解。

---

## 2. 為什麼這份文件要拆細

Priority 2 同時牽涉：

1. AI provider 接入與穩定化
2. 後端辨識邊界與 fallback
3. 候選修正 UI
4. confirm 與 nutrition estimate 的契約
5. 後續 re-estimation 與觀測性

若只放在總覽文件裡，容易讓人分不清：

1. 哪些是已經開始做的
2. 哪些只是方向，不是當前切片
3. 哪些屬於下一階段，而不是這一輪要一起做完

---

## 3. 目前狀態

目前可視為已知進度如下：

1. analysis upload -> recognition provider -> normalization 的後端邊界已形成
2. GPT / OpenAI 單一 provider 路徑已接入，並已可用真實圖片手動驗證食物候選辨識
3. confirm 已從「不在白名單就 400」改成較可完成的 fallback 路徑
4. candidate review UI 已開始補可改單位、刪除誤判、手動新增食物
5. 圖片上傳後的辨識流程，已把「AI 可恢復失敗」和「真正請求錯誤」分開處理，並已補出正式 `recognition_status` 回應欄位；`success`、`partial`、`complete_failure` 三種狀態均已可由 API 與前端分流
6. `partial` 判定規則已落地：以 `confidence_score < 0.6` 為閾值，任何候選項低於閾值即觸發 `PARTIAL`，同步設定 `manual_review_required=true` 並顯示使用者提示；全部候選項高於閾值則為 `SUCCESS`；候選項為空則為 `COMPLETE_FAILURE`
7. `complete_failure` 情境已不再直接送進 confirm；目前前端會留在 start 階段並顯示重拍 / 換圖提示，analysis 狀態也會保留在 `draft` 以支援重新上傳
8. `re-estimate` 第一版 API 與前端互動已落地，使用者可在 Candidate Confirmation 補充備註，例如「我只吃半份」或「這不是甜不辣，是炸雞」，再取得一版 AI 新建議並選擇是否套用
9. `re-estimate` 失敗時的前端提示已補齊：AI 失敗時顯示「AI 重新估算失敗，你目前的修改都已保留，可以繼續手動調整或直接送出確認。」，不再顯示原始 HTTP 錯誤訊息，使用者可確認編輯未消失

目前仍未完成的重點：

1. candidate review 還需要完整手機手動驗證。雖然目前已可承接 AI 候選、手動新增與 AI 新建議套用，但仍需要實際驗證手機操作是否順手，以及建議套用是否會造成使用者混淆。這一段要補，是為了確認使用者只需要做少量修正，而不是被迫重建整份餐點。
2. `re-estimate` 目前是第一版能力，已能吃到目前表單內容與備註，但還沒補到更細的建議對位規則，例如逐項套用、差異標示、名稱校正與份量校正的更細分類。這一段要補，是為了把 AI 校正從可用版本收斂成穩定體驗。
3. 最小觀測性還沒補齊，因為現在多半還是靠人工看 log 才知道 provider 是 timeout、配額不足、圖片資料錯誤，還是單純沒有可靠候選。這一段要補，是為了讓後續能判斷完全失敗率、部分成功率與 `re-estimate` 採用率，而不是每次都靠猜。

目前進度判定：Priority 2 不是「尚未接真實 AI」，而是「GPT / OpenAI 辨識已接上，正在從可用最小版收斂成可驗收的 V1.0 Release 能力」。

---

## 4. 目標

讓使用者在真實圖片上傳後，系統能依辨識結果進入三種清楚的處理方式：

1. 成功：直接進入確認流程，必要時只做少量修正
2. 部分成功：進入 candidate review，讓使用者微調、刪除誤判或補少量食物
3. 完全失敗：直接顯示辨識失敗，請使用者重拍或換圖，而不是要求使用者自行補完整份餐點資料

---

## 5. 工作拆解

### P2-01 辨識邊界與單一 provider

狀態：已完成最小版，後續以穩定性驗收為主。

目標：先把真實圖片主鏈打通，而不是一開始追求多 provider。

包含：

1. upload service 與 provider 邊界
2. 單一 provider 接入
3. 最小可用 prompt
4. normalization 與 candidate response

### P2-02 辨識失敗分流策略

狀態：已完成。`success`、`partial`、`complete_failure` 三種狀態均已落地，`partial` 以 `confidence_score < 0.6` 為判定閾值。

目標：讓 AI 結果依可用程度進入不同處理路徑，而不是所有失敗都導向人工補填。

包含：

1. 完全失敗時的重拍 / 換圖引導
2. 部分成功時的 candidate review 承接
3. timeout 與 provider error handling
4. 不讓可恢復失敗直接變成系統中止

### P2-03 Candidate Confirmation 修正體驗

狀態：已完成可用版，仍需手機手動驗收與 re-estimate 套用體驗收斂。

目標：把 candidate review 定位成「部分成功時的輕量修正工具」。

包含：

1. 編輯名稱
2. 調整份量
3. 調整單位
4. 刪除誤判
5. 視需要補少量漏掉項目

### P2-04 confirm 與營養估算契約

目標：讓 confirm 不再與 rigid food whitelist 綁死。

包含：

1. fallback-friendly contract
2. metadata 與估算來源
3. 盡量以 g 作為計算基準

### P2-05 re-estimation 能力

目標：在 candidate review 可用後，再補第二層效率工具。

包含：

1. 使用者修改後再次請 AI 估算
2. 使用者可補充備註或校正指令，例如「我只吃半份」或「這不是甜不辣，是炸雞」
3. 不直接覆蓋使用者最後輸入
4. 保留人類最終確認權

### P2-06 最小觀測性

目標：讓後續調 prompt、模型與 provider 時有可讀依據。

包含：

1. latency
2. timeout
3. error rate
4. complete failure rate
5. correction rate
6. re-estimation usage rate

### 目前程式實作規劃

目前這條主線的實作規劃，以「完全失敗 -> 重拍、部分成功 -> candidate review、成功 -> 直接確認」為產品方向，分成 4 個責任層來收斂：

1. 先整理 AI provider 的失敗類型，讓系統能分辨哪些屬於可恢復失敗，哪些屬於真正不合法的請求 ✅ 已完成
2. 再把辨識結果改成可表達狀態的結果物件，而不是只回傳候選清單，讓後續流程能分辨成功、部分成功與完全失敗 ✅ 已完成（含 `partial` 閾值判定）
3. 接著讓圖片上傳回應能直接帶出狀態與提示訊息，避免前端只能靠候選是否為空來猜目前發生了什麼事 ✅ 已完成
4. 最後由前端承接這些狀態：部分成功時進入 candidate review；完全失敗時直接顯示辨識失敗並引導重拍或換圖 ✅ 已完成

目前 4 層均已落地。剩餘工作為：手機手動驗收（P2-03）、re-estimate 建議對位精修（P2-05）、最小觀測性（P2-06）。

### 完成後如何更新文件

後續每完成一段程式調整並通過對應驗證後，應同步回寫這份文件的三個地方：

1. `目前可視為已知進度如下`：補上這次已經落地的能力
2. `目前仍未完成的重點`：移除已完成項目，或改寫成剩餘風險
3. `目前程式實作規劃`：標記哪一段已開始落地，哪一段仍在後續階段

原則是：已完成的內容要搬到進度區，不要一直停留在規劃區；這樣文件才不會落後於實作。

---

## 6. 推進順序

建議順序如下：

1. 先讓真實圖片候選主鏈可回傳可用結果
2. 再補辨識結果分流，明確區分成功、部分成功與完全失敗
3. 接著把部分成功時的 candidate review 修正體驗做順
4. 然後收斂 confirm 與 nutrition contract
5. 最後再補 re-estimation 與觀測性

這個順序的理由是：

1. 先把主鏈打通後，才有基礎判斷哪些情境屬於成功、哪些屬於部分成功、哪些屬於完全失敗
2. 若失敗分流沒有先定清楚，candidate review 很容易又被誤用成 AI 完全失敗時的人工補填流程
3. 若 candidate review 還不順，太早補 re-estimation 只會增加混亂
4. 若沒有觀測性，後續 prompt 與 provider 調整會失去判斷依據

---

## 7. 明確不做

1. 多 provider 切換平台
2. 完整食物資料庫搜尋
3. 一開始就追求極致辨識準確率
4. 把 AI 估出的營養值直接當唯一真相

---

## 8. 驗收條件

1. `/analyses/{id}/image` 可從真實圖片回傳狀態明確的辨識結果
2. AI 完全失敗時，系統會明確告知辨識失敗並引導重拍或換圖
3. AI 部分成功時，使用者可透過 candidate review 完成少量修正
4. candidate review 至少支援編輯名稱、份量、單位、刪除與新增項目
5. confirm 不會再因 rigid whitelist 或 rigid unit contract 導致主鏈中斷
6. 至少有最小量測可觀察 timeout、error、完全失敗率與部分成功率

---

## 9. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. 真實 AI 細規格： [真實-AI-食物辨識-MVP-規格-v1.md](./%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98-MVP-%E8%A6%8F%E6%A0%BC-v1.md)
3. Step 2 邊界： [../setup/Step2-核心開發任務清單-v1.md](../setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md)
