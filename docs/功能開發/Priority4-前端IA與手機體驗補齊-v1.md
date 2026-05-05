# Priority 4｜前端 IA 與手機體驗補齊 v1

- 文件名稱：Priority 4｜前端 IA 與手機體驗補齊
- 版本：v1
- 日期：2026-04-26
- 狀態：Draft
- 用途：把目前偏最小版的前端殼，補成更接近 PRD v1 的可用產品體驗

---

## 1. 文件定位

本文件處理的是 PRD v1 gap-closing plan 中的 Priority 4。

本 Priority 不在重新定義功能，而是在補齊使用者可見的頁面結構、空狀態、錯誤狀態與手機優先體驗。

---

## 2. 目前問題

目前前端主鏈可跑，但仍偏最小實作：

1. Landing / Home / Theme 等頁面結構還不夠完整
2. 一些流程仍較像開發驗證頁，而不是產品頁
3. 手機上雖可操作，但還沒有完整收斂到 PRD 想要的感受

---

## 3. 目前狀態

目前可視為已知進度如下：

1. 前端已具備登入、建檔、分析、結果與歷史等主要主鏈頁面
2. Theme preference、Profile、Analysis 與 History 的基本操作能力已存在
3. candidate review UI 已開始補齊可編輯名稱、份量、單位、刪除與手動新增等修正能力
4. 第一輪手機實測已確認 re-estimate / AI 校正雖功能可用，但目前把「AI 校正」輸入區與「AI 新建議」直接堆在同頁下方，手機上缺少明確焦點切換

目前仍未完成的重點：

1. Landing / Home / Theme Preference / Consent Review 等頁面仍未整理成較完整的產品頁結構
2. 空狀態、錯誤狀態與 helper copy 仍有不少區塊偏向開發驗證語氣
3. 手機優先排版雖可用，但整體節奏、導引與畫面連續性仍待收斂
4. Priority 1 已完成 Consent 與非醫療提醒最小版；後續若要繼續打磨 legal footer、review dialog、inline note 與 recommendation 區塊節奏，應納入本 Priority 的整體 IA 與手機體驗精修，而不是繼續擴張 Priority 1
5. AI 校正 / 新建議比較流程尚未形成清楚的第二層互動結構，仍偏向開發驗證頁

---

## 4. 目標

讓使用者在手機上能更自然地完成：

1. 建檔
2. 分析
3. 查看結果
4. 回看歷史

同時降低「像測試頁」的感受，提升產品連續性。

---

## 5. 工作拆解

### P4-01 Landing / Home 補強

### P4-02 Candidate review / result / history 的手機動線微調

補充本輪手機實測後的焦點：

1. AI 校正入口不應長駐在 confirm 頁底部，應改成明確 CTA 觸發的第二層互動。
2. 建議評估 modal 或 bottom sheet 承接「補充描述給 AI」的輸入，而不是在主頁面堆疊第二個表單。
3. 送出校正後，畫面應有獨立等待狀態，再進入比較與套用，而不是把原輸入區、舊內容、新建議全部同時留在頁面上。
4. 「目前內容」與「AI 新建議」應提供清楚切換或比較視圖，至少支援保留目前內容、查看校正前內容 / 切回原內容、再次校正三種動作。

2026-05-05 新增待辦：

1. loading state 視覺微調：將「照片辨識中」圖案或文字移到卡片右側，降低標題區擁擠感。參考：`S__93282310_0.jpg`
2. re-estimate 文案收斂：移除「目前版本與 AI...」說明段落，並把「AI 新版」按鈕改為「新的內容」，降低技術感。參考：`S__93282309_0.jpg`
3. start analysis 首屏精簡：移除 `Quick start` 區塊，將「改用本機圖片測試」改為「上傳圖片」，並修正手機板跑版。參考：`S__93249538.jpg`
4. candidate review 壓縮行高：label 與 value 保持同一行，避免欄位上下換行浪費垂直空間。參考：`S__93241351_0.jpg`
5. re-estimate 決策區減鈕：重新整理按鈕層級與主要 CTA，避免使用者在 confirm 頁不知道下一步。參考：`S__93241350_0.jpg`
6. result / history metric card 壓縮：卡片內改為單行資訊，例如「總熱量 420 kcal」，避免一個值拆成多行。參考：`S__93241348_0.jpg`

建議切片：

1. 可先做一個 P4-02A「手機資訊密度與文案降噪」小切片，先處理第 1、2、3、4、6 項，屬於低風險高可見度調整。
2. 第 5 項牽涉 re-estimate 流程按鈕層級，建議與第 2 項一起設計，不要獨立零碎修補。

### P4-03 Theme Preference 與 Consent Review 的頁面結構補齊

包含：

1. 將 Consent / legal review 相關低頻入口放進整體 Home / Profile / footer IA 中檢查
2. 驗證頁尾 legal dialog、inline non-medical note 與 recommendation 區塊在手機上的掃讀節奏
3. 若後續 legal / wellness guidance 提醒類型變多，再評估是否抽成共用 note 或 modal component

### P4-04 錯誤、空狀態與 helper copy 收斂

補充焦點：

1. AI 校正等待中的 loading / helper copy 也應納入本 Priority 的手機體驗語氣收斂。
2. 若後續沿用 modal / bottom sheet，需一併定義空回覆、失敗重試與再次校正的狀態文案。

---

## 6. 明確不做

1. 大規模設計系統重做
2. 超出 MVP 的多主題模式擴張
3. 完整無障礙重構專案

---

## 7. 驗收條件

1. 核心主鏈在手機上可順暢操作且無明顯卡點
2. 主要頁面不再只剩最小測試感結構
3. 錯誤、空狀態與導引文案足以支撐第一次使用者
4. AI 校正 / 新建議在手機上具備清楚的第二層互動結構，不再讓使用者在 confirm 頁面下方迷路

---

## 8. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. IA： [../IA-User-Flows-v1.md](../IA-User-Flows-v1.md)
3. 手機實測紀錄： [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)
