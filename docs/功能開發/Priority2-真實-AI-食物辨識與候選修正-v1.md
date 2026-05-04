# Priority 2｜真實 AI 食物辨識與候選修正 v1

- 文件名稱：Priority 2｜真實 AI 食物辨識與候選修正
- 版本：v1
- 日期：2026-05-01
- 狀態：V1.X 收斂中，P0/P1 與 P2-2 均已完成；剩餘 P2 為手機驗測
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
10. 最小觀測性結構化 log 已落地：後端三個服務（`recognition_openai.py`、`analysis_recognition.py`、`analysis_reestimate.py`）均已補入 `app.analysis` logger，記錄 `openai_recognition`、`openai_reestimate`、`recognition_result`、`reestimate_result` 事件，包含 `outcome`、`reason`、`candidate_count`、`latency_ms` 欄位
11. 低信心候選項視覺提示已落地：前端 candidate review 中 `confidence_score < 0.6` 的卡片加上橙色邊框與淡橙背景（`.is-low-confidence`），並在 support row 顯示「AI 對這項食物信心不足，建議確認名稱與份量。」
12. confirm 階段已改成 profile 不完整時仍可完成主鏈：後端不再因 `weight_kg`、`activity_level`、`goal_type` 缺漏回 409，而是改回傳 `source="generic"` 的通用建議；前端 confirm 會先提示「這次會先產生通用建議」，result 與 history detail 也會明確標示「通用建議」並提示補完 profile 後可得到更貼近的建議
13. 2026-05-04 已完成第一輪手機實測：真實圖片主鏈可跑通，塑膠瓶飲料可被辨識為 tea drink / 黑咖啡類候選，故意拍衛生紙時也能正確進入 complete failure 的重拍提示；詳細紀錄見 [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)

目前仍未完成的重點：

1. 第一輪手機手動驗證已完成，但仍有兩個 P2 收尾項目尚未收斂：上傳後缺少明確的辨識中狀態回饋，以及 re-estimate 在手機上的最小互動焦點仍不夠清楚。
2. 真實案例已驗證營養可信度風險，例如黑咖啡被估成 420 kcal；此問題不再屬於 P2 分流本身，而應移交 Priority 3 處理 nutrition source / estimation strategy。

目前進度判定：Priority 2 核心主鏈（辨識分流、candidate review、re-estimate、觀測性、低信心 UI、generic recommendation fallback）均已落地；P2-1 第一輪手機實測亦已完成，剩餘為兩個直接影響手機理解性的收尾項目，不影響主鏈通行，但建議在關閉 P2 前補齊。

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

狀態：已完成。`app.analysis` logger 已落地，涵蓋 provider latency、error type、recognition status、re-estimate outcome。

目標：讓後續調 prompt、模型與 provider 時有可讀依據。

包含：

1. latency ✅
2. timeout ✅（以 `reason: provider_timeout` 記錄）
3. error rate ✅（quota_exceeded / invalid_image / provider_unavailable）
4. complete failure rate ✅（`recognition_result` outcome=complete_failure）
5. partial rate ✅（`recognition_result` outcome=partial）
6. re-estimation outcome ✅（`reestimate_result` outcome=success/failure/fallback）

### 目前程式實作規劃

目前這條主線的實作規劃，以「完全失敗 -> 重拍、部分成功 -> candidate review、成功 -> 直接確認」為產品方向，分成 4 個責任層來收斂：

1. 先整理 AI provider 的失敗類型，讓系統能分辨哪些屬於可恢復失敗，哪些屬於真正不合法的請求 ✅ 已完成
2. 再把辨識結果改成可表達狀態的結果物件，而不是只回傳候選清單，讓後續流程能分辨成功、部分成功與完全失敗 ✅ 已完成（含 `partial` 閾值判定）
3. 接著讓圖片上傳回應能直接帶出狀態與提示訊息，避免前端只能靠候選是否為空來猜目前發生了什麼事 ✅ 已完成
4. 最後由前端承接這些狀態：部分成功時進入 candidate review；完全失敗時直接顯示辨識失敗並引導重拍或換圖 ✅ 已完成

目前 4 層均已落地，P1（觀測性 log + 低信心 UI）與 P2-2（generic recommendation fallback + 通用建議標示）亦已完成。P2-1 第一輪手機手動驗測已完成；剩餘工作為 upload / recognition loading state 與 re-estimate 手機互動收斂。

### P2-1：手機 UX 實際驗測

狀態：第一輪已完成，詳細紀錄見 [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)。

性質：手動驗測任務，無法自動化。

驗測流程：

1. 以已登入狀態進入 analysis
2. 上傳圖片，等待辨識（success / partial / complete_failure 各測一次）
3. candidate review：刪除、編輯名稱、改份量、改單位
4. re-estimate：輸入備註，確認 AI 建議面板出現，並驗證使用者是否能理解目前內容與 AI 新建議的關係
5. 完成確認，確認 result / history 頁面數字與摘要合理

重點關注：

- 刪除與確認按鈕觸控區大小（建議 min 44px）
- re-estimate 備註輸入框在鍵盤彈出時是否被遮擋
- low-confidence 橙色卡片在手機螢幕上是否顯眼
- footer-actions 按鈕是否被 iOS Safari 底部 home indicator 覆蓋
- 圖片上傳後是否有足夠明確的辨識中狀態
- AI 校正 / 新建議區塊是否會讓使用者在手機上失去焦點

本輪實測後的判讀：

1. success / complete_failure 方向成立，故意拍非食物時也能正確回到重拍提示。
2. re-estimate 已具備功能可用性，但手機互動結構仍偏像開發驗證頁，而不是收斂後的產品流程。
3. 若只做最小收尾，Priority 2 應至少補上 loading state 與 re-estimate 焦點收斂；若要做 modal / 分頁式比較體驗，則可移交 Priority 4。

### P2-2：profile 不完整時改走通用建議

狀態：已完成。

根本問題：原本後端 `require_recommendation_profile()` 會要求 `weight_kg`、`activity_level`、`goal_type` 三者都存在，否則 confirm 直接回 409。這會讓使用者走到最後一步才被擋住，也看不出系統到底是失敗、還是只是缺少個人化條件。

目前方向：

1. profile 完整時，照常產生 `personalized` recommendation
2. profile 不完整時，不阻擋 confirm，改產生 `generic` recommendation
3. generic recommendation 採固定一組比較中性的通用目標與活動建議，並明講這只是暫時參考
4. result 頁面與 history detail 頁面都必須明確標示「通用建議」
5. history list 第一版先不額外加標記，避免擴大 UI 變更範圍

本次改動：

1. `backend/app/services/analysis_confirm.py`：將 confirm 流程從「profile 不完整就 409」改成雙路徑。完整 profile 走既有個人化計算；不完整 profile 改走 generic target / generic exercises builder，並在 snapshot 寫入 `source`
2. `backend/app/db/models.py`、`backend/app/schemas/analysis.py`、`backend/app/services/analysis_views.py`：替 recommendation snapshot / response 補上 `source: personalized | generic` 與 generic guidance note
3. `frontend/src/App.tsx`：confirm stage 在送出前顯示 warning banner，告知本次會先產生通用建議；result 與 history detail 根據 `source === "generic"` 顯示「通用建議」與補完 profile 提示
4. `frontend/src/styles.css`：新增 `.status-banner.is-warning` 與 `.inline-text-button`，讓 generic 提示以提醒樣式呈現，而不是錯誤樣式

驗測步驟：

1. 不填個人資料，進 analysis → confirm stage → 確認出現橙色提示與「前往填寫 profile」按鈕
2. 直接點「完成確認」→ 成功進入 result，且 recommendation 區塊顯示「通用建議」與補完提示
3. 進 history detail → 確認同一筆 analysis 仍顯示「通用建議」標記
4. 補完三個欄位後重新分析 → 確認 result 不再顯示 generic 提示，而改為 personalized recommendation

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
6. 至少有最小量測可觀察 timeout、error、完全失敗率與部分成功率 ✅ 已完成

---

## 9. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. 真實 AI 細規格： [真實-AI-食物辨識-MVP-規格-v1.md](./%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98-MVP-%E8%A6%8F%E6%A0%BC-v1.md)
3. Step 2 邊界： [../setup/Step2-核心開發任務清單-v1.md](../setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md)
4. 第一輪手機驗測紀錄： [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)
