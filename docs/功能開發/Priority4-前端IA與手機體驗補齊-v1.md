# Priority 4｜前端 IA 與手機體驗補齊 v1

- 文件名稱：Priority 4｜前端 IA 與手機體驗補齊
- 版本：v1
- 日期：2026-04-26
- 最後更新：2026-05-09
- 狀態：Completed
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

## 5. 工作拆解與完成紀錄

### P4-02A 手機資訊密度與文案降噪 ✅

已完成（2026-05-09）：
1. loading badge 移至卡片右側，降低標題區擁擠感
2. re-estimate 說明段落移除，降低技術感
3. Quick start 區塊移除，上傳圖片入口簡化
4. candidate review 欄位壓縮為單行
5. metric card 改為單行顯示（總熱量 X kcal）

### P4-02 Re-estimate 流程重構 ✅

已完成（2026-05-09）：
1. re-estimate 入口改為文字觸發連結，不再長駐底部
2. 輸入區改為 bottom sheet（fixed + overlay），手機上有獨立焦點
3. 送出後 sheet 關閉，進入獨立 loading 狀態

### P4-04 錯誤、空狀態與 helper copy 收斂 ✅

已完成（2026-05-09）：
1. History 頁標題改為中文，移除開發票號 kicker
2. 所有 loading 文字統一為「載入中...」
3. 空紀錄提示改為對新使用者友善的說明
4. Profile / History 相關錯誤與成功訊息全改為中文
5. 分析流程 helper copy 移除英文技術詞

### P4-01 Landing / Home 補強 ✅

已完成（2026-05-09）：
1. 移除 `backend-badge`（開發 API URL 顯示）
2. Landing h1 改為產品文案「拍張照，知道你吃了什麼」
3. 主卡片改為產品導向說明，移除技術架構描述
4. 第二卡片從「驗收重點」改為「功能亮點」三步驟介紹

### P4-03 Theme Preference 與 Consent Review 補強 ✅

已完成（2026-05-09）：
1. 主 tab 標籤全改為中文（分析 / 紀錄 / 個人資料）
2. Theme Preference kicker 改為「視覺主題」
3. Profile 側欄移除開發說明文字

---

## 6. 明確不做

1. 大規模設計系統重做
2. 超出 MVP 的多主題模式擴張
3. 完整無障礙重構專案

---

## 7. 驗收條件

1. ✅ 核心主鏈在手機上可順暢操作且無明顯卡點
2. ✅ 主要頁面不再只剩最小測試感結構
3. ✅ 錯誤、空狀態與導引文案足以支撐第一次使用者
4. ✅ AI 校正 / 新建議在手機上具備清楚的第二層互動結構（bottom sheet），不再讓使用者在 confirm 頁面下方迷路

---

## 8. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. IA： [../IA-User-Flows-v1.md](../IA-User-Flows-v1.md)
3. 手機實測紀錄： [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)
