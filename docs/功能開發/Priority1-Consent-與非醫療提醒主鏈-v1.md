# Priority 1｜Consent 與非醫療提醒主鏈 v1

- 文件名稱：Priority 1｜Consent 與非醫療提醒主鏈
- 版本：v1
- 日期：2026-04-26
- 狀態：Draft
- 用途：把 PRD v1 尚未補齊的 Consent 與非醫療提醒主鏈拆成可追蹤的補完項目

---

## 1. 文件定位

本文件處理的是 PRD v1 gap-closing plan 中的 Priority 1。

它不是新的 PRD，也不是 Step 2 ticket 清單。

本文件只回答三件事：

1. 這條主鏈目前還缺什麼
2. 要先補哪些使用者可見流程
3. 什麼叫做這個 Priority 已經補齊

---

## 2. 目前問題

目前 repo 已有 Consent API、政策版本保存、consent 狀態檢查能力，以及前端最小版 Consent Intro。從使用者角度，剩下的缺口主要不是「沒有聲明內容」，而是顯示策略與流程收口仍需整理：

1. 首次同意主鏈需維持清楚、可理解、可完成，並避免被一般頁尾回看入口取代
2. 日常頁面不應常駐大段隱私與聲明內容，應改為頁面最下方的輕量文字連結
3. Analysis Result、History Detail 等建議相關畫面仍需保留短版非醫療提醒，但不需要佔用大面積卡片
4. 未同意前的 analysis 與 guidance 相關 guard 已補上 current consent 保護，日常頁面也已改為頁尾輕量回看入口；Analysis Result 與 History Detail 已改為 recommendation 區塊附近的短版提醒

---

## 3. 目前狀態

目前可視為已知進度如下：

1. 後端已具備 consent 紀錄、版本保存與狀態查詢能力
2. 前端已有最小版 Consent Intro，可顯示隱私政策與非醫療用途聲明摘要、展開內容與兩個 checkbox
3. consent 相關文案已有草稿與獨立文件，可作為前端導入基礎
4. 系統邏輯上已經把 consent 視為正式資料，而不是一次性的靜態頁面
5. Analysis 建立、confirm、re-estimate、History List 與 History Detail 已套用最新版必要同意保護
6. 完成同意後，會員主要頁面底部已提供「隱私政策」與「非醫療用途聲明」文字連結，並以輕量 dialog 回看內容
7. Analysis Result 與 History Detail 已移除大型 DisclaimerCard，改在 recommendation 區塊附近顯示短版非醫療提醒
8. 手機實機驗收已完成，Consent Intro、頁尾回看入口與短版提醒在最小版流程上可接受
9. Consent Intro 閱讀體驗已精修，包含第一眼文案、accordion 摘要、checkbox 區分與貼近操作的錯誤提示

目前仍未完成的重點：

1. Priority 1 主鏈與閱讀精修已完成最小版
2. 若要進一步打磨，建議移交 Priority 4，納入整體前端 IA 與手機體驗補齊

---

## 4. 目標

讓使用者從首次登入到第一次完成分析時：

1. 能清楚看到隱私政策與非醫療用途說明
2. 必須完成兩項同意後才進入建議流程
3. 完成同意後，在所有主要頁面最下方都能用輕量文字連結回看隱私與聲明內容
4. 在 Analysis Result、History Detail 等關鍵建議畫面，以短版提醒維持非醫療用途脈絡，不讓聲明內容佔用主要任務畫面

---

## 5. 工作拆解

### P1-01 首次登入導入

狀態：已完成最小精修。

目標：首次登入後先看到 Consent Intro，而不是直接略過。

包含：

1. consent 狀態判斷與轉向
2. Intro 卡片與簡短說明
3. 手機上可閱讀的文案結構

### P1-02 勾選與送出主鏈

狀態：已完成最小精修。

目標：讓兩項同意可被清楚閱讀、勾選與送出。

包含：

1. 隱私政策 checkbox
2. 非醫療用途說明 checkbox
3. 兩者都勾選後才可繼續
4. 文案區塊可收合，降低手機壓力

### P1-03 分析流程前置保護

目標：未同意前不得直接進入分析與建議流程。

包含：

1. analysis 入口前的 consent 檢查
2. confirm 或 re-estimate 前的 consent guard
3. History List 與 History Detail 的 guidance read-path guard
4. 錯誤訊息與返回 consent 的導引

### P1-04 非醫療提醒覆蓋

狀態：已完成最小版。

目標：在結果與歷史相關頁面補齊短版提醒，並避免大面積聲明卡片干擾主要任務。

包含：

1. Analysis Result 在 recommendation 附近顯示短版非醫療提醒
2. History Detail 在建議快照附近顯示短版非醫療提醒
3. 相關建議區塊保留 wellness guidance 語氣
4. 不要求在每個建議畫面顯示完整聲明段落或大型 legal card

目前實作：Analysis Result 的「每日目標與推薦運動」與 History Detail 的「當次建議快照」已改用 inline note 顯示非醫療提醒，不再於結果頂部或 snapshot 後常駐大型聲明卡片。

### P1-05 全站頁尾回看入口

狀態：已完成最小版。

目標：讓使用者在完成同意後，能隨時從頁面最下方回看隱私與聲明內容。

包含：

1. 所有會員狀態主要頁面最下方顯示「隱私政策」與「非醫療用途聲明」文字連結
2. 連結可導向同頁的輕量 review 區塊、獨立 review view，或後續正式 policy page
3. 頁尾入口只作為日常回看，不取代首次必要同意與 checkbox
4. 頁尾不常駐完整聲明段落，避免壓縮 Analysis、History、Profile 等主要任務空間

目前實作：登入後主畫面底部顯示兩個文字連結，點擊後以同頁輕量 dialog 顯示對應版本內容；此入口只提供日常回看，不影響首次必要同意流程。

---

## 6. 明確不做

1. 法務後台
2. 多版本政策管理介面
3. 額外登入方式管理
4. 超出 MVP 的合規流程擴張
5. 在每個頁面常駐完整隱私政策或完整非醫療聲明內容

---

## 7. 驗收條件

1. 首次登入後，使用者會先進入 Consent Intro
2. 未勾選兩項同意前，不能進入分析與建議流程
3. 完成同意後，主要頁面最下方皆有可回看隱私政策與非醫療用途聲明的文字連結
4. Analysis Result 與 History Detail 皆可看到短版非醫療用途提醒，但不以大型聲明區塊佔據主要畫面
5. 手機版上，首次同意文案可閱讀；日常頁面不形成過重資訊牆

---

## 8. 對應文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. 範圍基線： [../setup/Step2-核心開發任務清單-v1.md](../setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md)
3. 畫面與流程： [../IA-User-Flows-v1.md](../IA-User-Flows-v1.md)
