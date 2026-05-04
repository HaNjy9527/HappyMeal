# Priority 3｜正式營養資料來源與估算策略 v1

- 文件名稱：Priority 3｜正式營養資料來源與估算策略
- 版本：v1
- 日期：2026-04-26
- 狀態：Draft
- 用途：把營養估算從 demo 級 preset mapping，補成可持續使用的 MVP 級策略

---

## 1. 文件定位

本文件處理的是 PRD v1 gap-closing plan 中的 Priority 3。

它的任務不是重做整條分析流程，而是補齊「辨識之後，營養值到底怎麼來」這個核心缺口。

---

## 2. 目前問題

目前營養 totals 與建議可以產出，但主要仍建立在 preset mapping 上。

這代表：

1. 已知少數食物可以成立
2. 真實辨識接上後，未知食物與未知單位會迅速擴大
3. 若沒有較正式的 nutrition source，history 與 recommendation 的長期價值會不足

---

## 3. 目前狀態

目前可視為已知進度如下：

1. confirm 已不再完全依賴 rigid food whitelist，未知食物與多種單位可以透過 fallback 路徑完成
2. 後端已開始保存 canonical food name、nutrition source、is_estimated、resolved_weight_g、weight_estimation_method 等 metadata
3. 系統已經朝向「盡量先轉成克重，再做營養估算」的方向收斂
4. 第一輪手機實測已出現真實失真案例：黑咖啡結果顯示約 420 kcal，但實際包裝標示約 7 kcal，代表 packaged drink 的 nutrition source / portion interpretation / fallback mapping 仍有明顯缺口

目前仍未完成的重點：

1. 正式 nutrition source 仍未接入，目前仍以 preset 與 fallback estimate 為主
2. canonical food mapping 策略仍屬第一版，尚未形成可持續擴充的正式資料層
3. 前端目前尚未完整呈現低噪音的估算來源提示與相關 UX 收斂
4. 包裝飲料案例顯示 unit normalization、每份容量換算與 nutrition source 命中策略尚未可靠，已足以影響 result 與 history 的可信度

---

## 4. 目標

建立一條可持續擴充的營養估算策略，使系統可以：

1. 盡量將輸入轉成 canonical food 與 g
2. 對已知食物命中正式資料來源
3. 對未知食物仍提供可完成流程的估算
4. 在必要時標示估算性質，但不讓使用者被技術細節淹沒

---

## 5. 工作拆解

### P3-01 canonical food mapping

目標：先把 food name 與 normalized food name 對齊到較穩定的 canonical key。

### P3-02 unit normalization

目標：盡量將輸入單位轉成 g，降低後續計算分歧。

補充焦點：

1. 包裝飲料需要補強 ml / bottle / can / serving 與 g 或每份營養標示之間的換算策略。
2. 若辨識到的是「黑咖啡 / 茶飲 / 瓶裝飲料」這類 packaged drink，不應直接沿用高熱量餐食 fallback。

### P3-03 nutrition source 層級

目標：定義來源優先序。

建議順序：

1. 正式 nutrition source
2. canonical mapping 對應
3. 估算 fallback

補充焦點：

1. 需把黑咖啡 420 kcal 這類失真案例納入 source selection 驗證樣本。
2. packaged drink 若無法命中正式資料來源，fallback 也應有更保守的防呆，不可產生明顯違反包裝標示等級的結果。

### P3-04 metadata 與可追溯性

目標：保留來源與估算資訊，供系統與低噪音 UI 使用。

### P3-05 結果與建議整合

目標：讓 history 與 recommendation 可直接重用這套營養結果，而不是每次重新猜測。

補充焦點：

1. 需確認異常高熱量結果不會直接寫入 history 而破壞長期可信度。
2. 必要時應能利用 nutrition source / is_estimated / resolved_weight_g 等 metadata 幫助排查失真來源。

---

## 6. 明確不做

1. 完整食物搜尋資料庫前端
2. 醫療級營養建議
3. 每日長期飲食累積模型

---

## 7. 驗收條件

1. 真實辨識接上後，大多數常見餐點不會因食物 key 或單位而卡死
2. 營養結果來源具備最小可追溯性
3. 結果可被 history 與 recommendation 穩定重用
4. 包裝飲料案例不再出現黑咖啡約 7 kcal 卻被估成數百 kcal 的明顯失真

---

## 8. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. Priority 2： [Priority2-真實-AI-食物辨識與候選修正-v1.md](./Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md)
3. 手機實測紀錄： [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)
