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

目前仍未完成的重點：

1. Landing / Home / Theme Preference / Consent Review 等頁面仍未整理成較完整的產品頁結構
2. 空狀態、錯誤狀態與 helper copy 仍有不少區塊偏向開發驗證語氣
3. 手機優先排版雖可用，但整體節奏、導引與畫面連續性仍待收斂
4. Priority 1 已完成 Consent 與非醫療提醒最小版；後續若要繼續打磨 legal footer、review dialog、inline note 與 recommendation 區塊節奏，應納入本 Priority 的整體 IA 與手機體驗精修，而不是繼續擴張 Priority 1

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

### P4-03 Theme Preference 與 Consent Review 的頁面結構補齊

包含：

1. 將 Consent / legal review 相關低頻入口放進整體 Home / Profile / footer IA 中檢查
2. 驗證頁尾 legal dialog、inline non-medical note 與 recommendation 區塊在手機上的掃讀節奏
3. 若後續 legal / wellness guidance 提醒類型變多，再評估是否抽成共用 note 或 modal component

### P4-04 錯誤、空狀態與 helper copy 收斂

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

---

## 8. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. IA： [../IA-User-Flows-v1.md](../IA-User-Flows-v1.md)
