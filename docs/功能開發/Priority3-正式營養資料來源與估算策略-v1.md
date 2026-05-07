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

## 8. 2026-05-07 驗收補充

本次補充驗收的目的，不是新增功能，而是確認最近將 canonical food name 判定抽離後，既有 confirm 主鏈沒有被改壞，且 mapping 責任確實集中到單一模組。

### 8.1 驗收範圍

本次驗收聚焦三個面向：

1. `food_mapping` 單元測試是否穩定輸出相同 canonical key
2. `analysis_confirm` 整合流程是否維持既有 API 行為與 fallback 能力
3. `analysis_confirm` 是否已改為呼叫 `resolve_canonical_food`，而不是在服務內部分散判定

### 8.2 驗收方式

本次實際執行的驗收命令如下：

```powershell
$env:PYTHONPATH='D:\code\HappyMeal\backend'
.\.venv\Scripts\pytest.exe backend\tests\test_food_mapping.py -q
.\.venv\Scripts\pytest.exe backend\tests\test_analysis_draft.py -q
.\.venv\Scripts\pytest.exe backend\tests\test_analysis_draft.py -q -k "uses_canonical_food_mapping_module or accepts_unknown_foods"
```

補充說明：

1. 從 repo root 直接執行 backend 測試時，需要先把 `backend` 放進 `PYTHONPATH`，因為測試使用 `app.*` 匯入。
2. `.venv\Scripts\python.exe` 與 `.venv\Scripts\pytest.exe` 已確認可執行。

### 8.3 驗收結果

驗收結果如下：

1. `backend/tests/test_food_mapping.py`：`7 passed`
2. `backend/tests/test_analysis_draft.py`：`19 passed`
3. 聚焦回歸測試：`2 passed`

判讀結論：本次 canonical mapping 抽離後，既有 confirm 主鏈仍維持可用，沒有觀察到 API 行為回歸。

### 8.4 已驗收的 mapping 樣本

以下輸入已驗證會穩定得到相同 canonical 結果：

| 輸入 food_name | 輸入 normalized_food_name | 預期 canonical_food_name | 驗收狀況 |
| -------------- | ------------------------- | ------------------------ | -------- |
| Chicken Salad  | chicken_salad             | chicken_salad            | 通過     |
| 白飯           | white_rice                | generic_rice             | 通過     |
| 雞肉飯         | chicken_rice_bowl         | generic_mixed_meal       | 通過     |
| 辣椒醬         | mystery_condiment         | generic_condiment        | 通過     |
| 薑絲           | mystery_garnish           | generic_garnish          | 通過     |
| 雞肉飯         | mystery_lunch             | generic_mixed_meal       | 通過     |
| 神秘料理       | mystery_food              | generic_mixed_meal       | 通過     |

這代表目前 mapping 已涵蓋：

1. 已知 canonical key 直接命中
2. alias 命中
3. 關鍵字 fallback 命中
4. 未知食物 default fallback 命中

### 8.5 confirm 流程驗收重點

`analysis_confirm` 的整合驗收已確認以下行為未被改壞：

1. 回應仍會帶出 `canonical_food_name`
2. `nutrition_source` 仍維持既有字串，例如 `preset`、`alias_mapping`、`keyword_fallback`
3. 總熱量與三大營養素快照仍可正確保存與回傳
4. 未知食物與未知單位仍可透過 fallback 路徑完成 confirm 流程

補充觀察：

1. 既有測試仍有固定檢查 totals 快照，例如 `398.00 kcal`、`34.50 g protein`、`23.30 g fat`、`12.60 g carb`，本次驗收仍通過。
2. 未知食物案例仍可完成流程，且 `canonical_food_name` 與 `nutrition_source` 會落在 fallback 預期值。

### 8.6 名稱判定抽離驗收

本次最關鍵的回歸點已驗證通過：

1. `analysis_confirm` 的測試使用 monkeypatch 攔截 `app.services.analysis_confirm.resolve_canonical_food`
2. confirm 後可觀察到實際呼叫參數為 `("Chicken Surprise", "mystery_chicken")`
3. 回應中的 `canonical_food_name` 與 `nutrition_source` 會跟著 fake resolver 回傳值改變

判讀上，這表示 canonical food name 的判定責任已集中到 `resolve_canonical_food`，而不是散落在 `analysis_confirm.py` 內各自判斷。

### 8.7 Python 3.14 下 `asyncio.iscoroutinefunction` 棄用警告分析

本次測試全數通過，但在 Python 3.14 環境下會看到來自 FastAPI 的 warning：

```text
DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
```

目前判讀如下：

1. warning 來源不是 HappyMeal 專案程式碼，而是 `fastapi.routing` 內部仍呼叫 `asyncio.iscoroutinefunction(dependant.call)`。
2. 專案目前環境版本為 Python `3.14.0`、FastAPI `0.116.1`、Starlette `0.47.3`。
3. Python 3.14 已將 `asyncio.iscoroutinefunction` 標記為 deprecated，官方建議改用 `inspect.iscoroutinefunction`。
4. 本 warning 目前不影響 API 執行或測試結果，只會在測試或啟用 warning 顯示時出現噪音。
5. 若未來框架版本仍未調整，到了 Python 3.16 可能升級為實際相容性問題。

### 8.8 對專案的影響與建議處理

目前建議把這個 warning 視為「相容性追蹤項」，不是當前功能 blocker。

建議處理順序：

1. 優先關注 FastAPI 上游是否在後續版本將 `asyncio.iscoroutinefunction` 替換為 `inspect.iscoroutinefunction`。
2. 在正式升級到 Python 3.16 前，安排一次框架相容性驗證，避免 deprecated API 被移除後才發現問題。
3. 在 warning 尚未被上游修正之前，不建議為了壓掉訊息而在專案內加全域 warnings filter，避免掩蓋其他真正需要處理的 deprecation。
4. 若後續 CI 需要對 warning 採更嚴格政策，應先處理框架版本升級，再決定是否把 DeprecationWarning 視為失敗條件。

結論：canonical food mapping 抽離的功能驗收已通過；Python 3.14 warning 屬於外部框架相容性噪音，短期可接受，但中期需要透過 FastAPI 升級或相容性檢查收斂。

---

## 9. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. Priority 2： [Priority2-真實-AI-食物辨識與候選修正-v1.md](./Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md)
3. 手機實測紀錄： [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)
