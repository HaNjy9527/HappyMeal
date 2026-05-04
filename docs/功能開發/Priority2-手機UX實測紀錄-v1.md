# Priority 2｜手機 UX 實測紀錄 v1

- 文件名稱：Priority 2｜手機 UX 實測紀錄
- 版本：v1
- 日期：2026-05-04
- 狀態：第一輪手機實測完成
- 用途：記錄 Priority 2 真實圖片與手機操作驗測結果，作為是否可關閉 P2 與是否移交後續 Priority 的依據

---

## 1. 文件定位

本文件是 [Priority2-真實-AI-食物辨識與候選修正-v1.md](./Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md) 中 P2-1 手機 UX 實際驗測的第一輪紀錄。

它的目的不是重新描述規格，而是回答以下三件事：

1. 目前真實圖片主鏈是否已能跑通
2. 哪些問題屬於這次驗測已證實的風險
3. 哪些問題應留在 Priority 2 修正，哪些應移交後續 Priority

---

## 2. 驗測範圍

本輪以「已登入狀態」為前提，重點驗證 Priority 2 的核心主鏈，而非重新驗證 LINE Login。

本輪實測包含：

1. 真實圖片上傳與辨識結果分流
2. candidate review 的手機操作感受
3. re-estimate / AI 校正流程的可理解性
4. result / history 是否能反映分析結果

本輪不包含：

1. LINE Login regression 驗證
2. profile 不完整時 generic recommendation fallback 驗證
3. 正式營養資料來源正確性驗證

---

## 3. 驗測素材

本輪主要參考以下手動截圖與測試照片：

1. [test_image/S\_\_93241347_0.jpg](../../test_image/S__93241347_0.jpg)：history list，顯示黑咖啡分析後摘要與 420 kcal
2. [test_image/S\_\_93241348_0.jpg](../../test_image/S__93241348_0.jpg)：analysis result，黑咖啡結果為 420 kcal / 20g protein / 14g fat / 52g carb
3. [test_image/S\_\_93241349_0.jpg](../../test_image/S__93241349_0.jpg)：candidate confirmation，塑膠瓶飲料被辨識為「伯朗咖啡 黑咖啡」
4. [test_image/S\_\_93241350_0.jpg](../../test_image/S__93241350_0.jpg)：AI 校正區塊與 AI 新建議區塊在同頁下方出現
5. [test_image/S\_\_93241351_0.jpg](../../test_image/S__93241351_0.jpg)：另一筆真實圖片被辨識為 tea drink，顯示非餐盒類拍攝也可得出候選
6. [test_image/S\_\_93249538.jpg](../../test_image/S__93249538.jpg)：非食物圖片（衛生紙）進入 complete failure，引導重拍 / 換圖

---

## 4. 驗測結論摘要

本輪結論可先濃縮成 5 點：

1. 真實圖片辨識主鏈已可用，AI 對實物外觀的判斷比預期好，至少已能把塑膠瓶飲料辨識成茶類 / 黑咖啡類候選，而不是完全失敗。
2. complete failure 路徑有效，故意拍衛生紙時，系統沒有硬湊成食物，而是正確回到「這次沒有穩定辨識出食物」的重拍提示，這應視為成功案例。
3. 上傳後缺少明確的「正在辨識中」回饋，使用者會無法判斷目前是在等待 AI、請求卡住、還是系統沒有反應。
4. AI 校正 / 新建議目前直接堆在 confirm 頁面下方，手機上很難理解現在的主要任務是什麼，這已不是純文案問題，而是互動結構問題。
5. 黑咖啡營養結果明顯失真，這不是小誤差，而是會破壞結果可信度的問題；它不屬於辨識分流本身，而屬於 nutrition source / estimation strategy 的缺口。

---

## 5. 逐點觀察

### 5.1 真實圖片辨識能力：正向結果

觀察：

1. 使用塑膠瓶飲料測試時，AI 至少辨識出 tea drink 或黑咖啡類型，顯示 provider 對「包裝飲品」不是完全失效。
2. 這代表 Priority 2 的「真實圖片 -> 候選項目 -> candidate review」主鏈已具備基本可用性。

判讀：

1. 這一點支持 Priority 2 目前的核心判斷：辨識主鏈已通。
2. 後續若要改善，重點不是先懷疑 provider 完全不可用，而是處理 unit normalization 與 nutrition mapping 的可信度。

### 5.2 AI 校正 / 新建議 UX：主要風險

觀察：

1. 「AI 校正」輸入框與「AI 新建議」面板直接堆疊在 candidate review 下方。
2. 在手機畫面上，使用者很容易把它理解成同一頁裡又多出一個新表單，而不是一個可選的第二層工具。
3. 使用者輸入說明後，畫面同時保留原本內容與新建議，缺少清楚的焦點切換。

建議方向：

1. 先有一個明確 CTA，例如「校正 AI 建議」或「補充描述給 AI」。
2. 點擊後以 modal 或 bottom sheet 開啟輸入介面，而不是直接把輸入框常駐在主頁底部。
3. 送出後關閉輸入介面，進入清楚的等待狀態。
4. 新建議回來後，畫面應只聚焦在「目前內容」與「AI 新建議」的比較，不要同時保留整段說明區塊。
5. 建議提供 3 個明確動作：保留目前內容、查看校正前內容 / 切回原內容、再次校正。

判讀：

1. 這個問題雖然源自 Priority 2 的 re-estimate 功能，但暴露的是互動結構與手機 IA 問題。
2. 若只求 P2 最小可用收尾，至少要先把校正入口、等待狀態、建議套用焦點做清楚。
3. 若要做到較完整的 modal / 分頁式比較體驗，較適合納入 Priority 4 的手機 UX 收斂。

### 5.3 黑咖啡 420 kcal：結果可信度風險

觀察：

1. 黑咖啡分析結果顯示 420 kcal，但實際瓶身標示約為 7 kcal。
2. 這個落差已遠超過「估算值可接受誤差」範圍。
3. 問題看起來不是辨識出錯而已，而是辨識後的 nutrition source / portion interpretation / fallback mapping 明顯失真。

判讀：

1. 這一點不應視為 Priority 2 分流失敗，而應視為 Priority 3 的核心缺口已被真實案例驗證。
2. 這會直接影響 result 與 history 的可信度，因此優先級應高。

### 5.4 非食物圖片：complete failure 成功案例

觀察：

1. 故意拍衛生紙後，系統沒有硬產生食物候選。
2. 前端回到 start analysis，並顯示「AI 這次沒有穩定辨識出食物，請重拍或換一張更清楚的圖片」。

判讀：

1. 這是 Priority 2 成功案例，代表「完全失敗 -> 重拍 / 換圖」的分流方向成立。
2. 這個結果應明確寫回 Priority 2，作為 complete failure 驗收證據，而不是只記錄成功辨識案例。

### 5.5 上傳後沒有辨識中回饋：主鏈回饋缺口

觀察：

1. 提供圖片後，畫面缺少明顯的 in-progress state。
2. 即使後端正在呼叫 AI，使用者仍可能以為系統沒有工作。
3. 這種不確定感出現在主鏈最關鍵的一步，風險高於一般小 UI 細節。

建議方向：

1. 上傳成功後立即切到明確的「正在辨識中」狀態。
2. 顯示 loading 文案，例如「正在辨識圖片，通常需要幾秒鐘」。
3. 若等待超過一定時間，可補充次級提示，例如「仍在處理中，請稍候」。
4. 若失敗，再轉回目前既有的 complete failure 或 error message。

判讀：

1. 這屬於 Priority 2 範圍，因為它直接影響「上傳 -> 辨識 -> 分流」這條主鏈是否可理解。
2. 不建議把它延後到純前端精修階段才處理。

---

## 6. 問題歸屬建議

### 6.1 建議仍留在 Priority 2 的項目

1. 上傳後缺少明確辨識中狀態。
2. re-estimate 最小互動收斂：至少要讓入口、等待、建議套用三段更清楚，不要讓使用者在同頁迷路。
3. P2-1 手機驗測文件化與驗收結論回寫。

### 6.2 建議移交 Priority 3 的項目

1. 黑咖啡熱量與三大營養素明顯失真。
2. 包裝飲料的份量單位、克重換算與 nutrition source 對齊。

### 6.3 建議移交 Priority 4 的項目

1. AI 校正改成 modal / bottom sheet 的完整互動重構。
2. 「目前內容」與「AI 新建議」之間的切換式比較 UI。
3. candidate review 與 re-estimate 在手機上的整體頁面節奏重整。

### 6.4 不需要另外開項的事項

1. 衛生紙被判定為非食物，應直接記為 Priority 2 驗收成功案例。
2. 塑膠瓶飲料可被辨識為茶類 / 黑咖啡類，應記為 provider 已具備基本實物辨識能力的正向證據。

---

## 7. 對 Priority 2 狀態的影響

本輪實測後，較合理的判讀是：

1. Priority 2 核心主鏈已通，包含 success / partial / complete failure 三條路徑的方向都成立。
2. 但 P2-1 不應只標示為「尚未驗測」；更精確的說法是「第一輪手機實測已完成，已確認主鏈成立，但仍有兩個直接影響體驗理解的收尾項目」。
3. 這兩個收尾項目為：辨識中狀態回饋、re-estimate 最小手機互動收斂。
4. 營養可信度問題已被真實案例明確驗證，應正式回寫為 Priority 3 的高優先缺口。

---

## 8. 建議下一步

建議順序：

1. 先在 Priority 2 補上 upload / recognition loading state。
2. 再決定 Priority 2 是否只做 re-estimate 最小收斂，或直接把 modal / 切換比較 UI 移交 Priority 4。
3. 將黑咖啡案例帶入 Priority 3，作為 nutrition source / fallback mapping 的真實失真樣本。

---

## 9. 相關文件

1. 主文件： [Priority2-真實-AI-食物辨識與候選修正-v1.md](./Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md)
2. 後續營養可信度： [Priority3-正式營養資料來源與估算策略-v1.md](./Priority3-%E6%AD%A3%E5%BC%8F%E7%87%9F%E9%A4%8A%E8%B3%87%E6%96%99%E4%BE%86%E6%BA%90%E8%88%87%E4%BC%B0%E7%AE%97%E7%AD%96%E7%95%A5-v1.md)
3. 後續手機體驗補齊： [Priority4-前端IA與手機體驗補齊-v1.md](./Priority4-%E5%89%8D%E7%AB%AFIA%E8%88%87%E6%89%8B%E6%A9%9F%E9%AB%94%E9%A9%97%E8%A3%9C%E9%BD%8A-v1.md)
