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

1. 正式 nutrition source 已有本地策展版 MVP，但尚未接完整外部資料來源或完整食物資料庫
2. canonical food mapping 正式資料層第一版已落地，但 canonical coverage 仍有限，後續仍需依真實樣本擴充
3. 前端目前尚未完整呈現低噪音的估算來源提示與相關 UX 收斂
4. 包裝飲料案例已先以 drink fallback 收斂明顯失真，黑咖啡後續也已升級為 `official_source`；甜飲精度仍需更多真實樣本驗證

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

目前狀態：第一版正式資料層已完成。

2026-05-09 實作補充：

1. 已將 food name 判定責任自 `analysis_confirm` 抽離，集中到獨立的 `food_mapping` 模組。
2. 已建立單一入口 `resolve_canonical_food()`，輸入為 `food_name` 與 `normalized_food_name`，輸出為穩定的 canonical mapping 結果。
3. mapping 結果已固定包含 `canonical_food_name`、`match_type`、`matched_term`、`is_estimated`，供後端內部統一使用。
4. 已將 direct、alias、keyword、default fallback 四種名稱判定路徑整理為正式規則層，不再散落在 confirm 流程內。
5. `analysis_confirm` 現在只負責呼叫 canonical mapping、查對應 preset / nutrition source、再做份量與營養計算。
6. 對外 API shape 維持不變；`canonical_food_name` 持續回傳，`nutrition_source` 仍維持既有相容字串：
   `preset`、`alias_mapping`、`keyword_fallback`、`default_fallback`。

第一版 canonical coverage：

1. canonical key 沿用現有 preset 與 generic 類別，例如 `chicken_salad`、`boiled_egg`、`generic_mixed_meal`、`generic_rice`、`generic_vegetables`。
2. alias 第一版已固定包含 `chicken_rice_bowl`、`white_rice`、`cabbage`、`ginger_shreds`、`chili_sauce`。
3. keyword 規則第一版已固定優先序：`generic_condiment`、`generic_garnish`、`boiled_egg`、`generic_mixed_meal`、`generic_vegetables`、`generic_rice`、`generic_protein`、`default_fallback`。

目前邊界：

1. 本階段未新增資料庫 table 或 migration。
2. 本階段未建立完整食物資料庫或後台維護介面。
3. 本階段重點是把名稱判定抽成可維護資料層，不是一次補齊所有食物 coverage。

### P3-02 unit normalization

目標：盡量將輸入單位轉成 g，降低後續計算分歧。

目前狀態：Backend MVP 已完成。

補充焦點：

1. 包裝飲料需要補強 ml / bottle / can / serving 與 g 或每份營養標示之間的換算策略。
2. 若辨識到的是「黑咖啡 / 茶飲 / 瓶裝飲料」這類 packaged drink，不應直接沿用高熱量餐食 fallback。

2026-05-09 實作補充：

1. 已將份量換算責任自 `analysis_confirm` 抽離，集中到獨立的 `portion_resolution` 模組。
2. `analysis_confirm` 現在只負責組裝 confirm 主鏈；單位正規化、飲料判定、克重換算與 estimation method 命名都集中在單一模組。
3. 已保留既有 response shape，不新增公開 API 欄位；`portion_unit`、`source_portion_unit`、`resolved_weight_g`、`weight_estimation_method` 均沿用既有欄位。
4. 已補齊新的 unit alias：`ml`、`milliliter(s)`、`cc`、`l`、`liter(s)`、`bottle`、`bottles`、`can`、`cans`。
5. 非飲料情境仍沿用既有 `g`、exact unit match、family conversion、common serving fallback 流程，避免影響既有餐點 totals 快照。
6. 飲料情境新增容量導向換算規則：
   `ml / cc -> g`、`l -> 1000 ml`、`can -> 330 ml`、`bottle -> 375 ml`、`cup -> 240 ml`、`serving -> 240 ml`。
7. 已新增 packaged drink 判定 helper，依 `food_name` 與 `normalized_food_name` 內的 `black_coffee`、`americano`、`black_tea`、`green_tea`、`tea_drink` 與 `coffee / tea / drink / beverage` 關鍵字判定是否走飲料路徑。
8. 飲料若無法命中合適 preset，不再落回 `generic_mixed_meal`，而是改走低估保守的 `generic_unsweetened_drink` fallback。
9. `generic_unsweetened_drink` 暫時採 demo 級防呆值：
   每 `100 g` 為 `2 kcal`、`0 g protein`、`0 g fat`、`0.5 g carb`。
10. 已新增飲料專用 `weight_estimation_method`：
    `direct_milliliters`、`drink_container_default`、`drink_serving_default`。

本次 MVP 邊界：

1. 本階段不新增資料庫 migration，沿用既有 `weight_estimation_method` 字串欄位。
2. 本階段不新增前端 UI 或 response schema。
3. 本階段對可判定為飲料但甜度不明的候選，先採低估保守策略，避免再出現黑咖啡數百 kcal。
4. 甜飲精度、正式 nutrition source 與更細的包裝標示解析，留待 P3-03 處理。

### P3-03 nutrition source 層級

目標：定義來源優先序。

目前狀態：MVP 版已完成。

建議順序：

1. 正式 nutrition source
2. canonical mapping 對應
3. 估算 fallback

補充焦點：

1. 需把黑咖啡 420 kcal 這類失真案例納入 source selection 驗證樣本。
2. packaged drink 若無法命中正式資料來源，fallback 也應有更保守的防呆，不可產生明顯違反包裝標示等級的結果。

2026-05-09 實作補充：

1. 已新增 `nutrition_resolution` 統一介面，讓 confirm 流程透過 `resolve_item_nutrition()` 取得完整營養解析結果。
2. 已建立明確的 source decision flow：`official_source -> canonical_mapping -> fallback_estimate -> special_guard`。
3. 已新增本地策展版 `official_source` catalog，先納入少量高信心資料，例如黑咖啡、白飯、水煮蛋、雞胸與 leafy vegetables。
4. 黑咖啡已由 P3-02 階段的 `drink_fallback` 進一步升級為優先命中 `official_source`。
5. 茶飲等尚未列入 official catalog 的 packaged drink，仍可透過 `drink_fallback` 防呆。
6. 未知食物仍可透過 `default_fallback` 完成流程，不會因找不到正式來源而中斷。

本次 MVP 邊界：

1. 本階段不做完整食物搜尋資料庫，也不串外部 nutrition API。
2. 本階段不新增公開 API 欄位，也不新增資料庫 migration。
3. `nutrition_source` 可能出現新增值 `official_source`，但 response shape 維持不變。

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

## 9. 2026-05-09 P3-02 unit normalization 驗收補充

本次補充驗收的目的，是確認 P3-02 Backend MVP 已完成三個核心面向：

1. 責任抽離：`analysis_confirm` 已改為呼叫單一 `portion_resolution` 模組，而不是在服務內散落處理單位換算
2. 單位擴充：`ml / l / bottle / can / cup / serving` 的飲料換算規則已落地
3. 防呆收斂：黑咖啡與茶飲等 packaged drink 不再落回高熱量 mixed meal fallback

### 9.1 驗收範圍

本次驗收聚焦以下行為：

1. `portion_resolution` 單元測試是否正確覆蓋 `ml`、`l`、`bottle`、`serving` 與非飲料回歸案例
2. `analysis_confirm` 整合流程是否能正確回傳 `source_portion_unit`、`resolved_weight_g`、`weight_estimation_method`
3. 黑咖啡 / 茶飲案例是否改走 `drink_fallback`，不再出現數百 kcal 的明顯失真
4. 既有 `Chicken Salad` / `Boiled Egg` totals 與 unknown food fallback 是否維持既有行為

### 9.2 驗收方式

本次實際執行的驗收命令如下：

```powershell
$env:PYTHONPATH='D:\code\HappyMeal\backend'
& 'D:\code\HappyMeal\.venv\Scripts\python.exe' -m pytest backend\tests\test_portion_resolution.py -q
& 'D:\code\HappyMeal\.venv\Scripts\python.exe' -m pytest backend\tests\test_analysis_draft.py -q
& 'D:\code\HappyMeal\.venv\Scripts\python.exe' -m pytest backend\tests\test_food_mapping.py -q
```

補充說明：

1. 本次環境下 `pytest.exe` 啟動器不可直接使用，因此改用 `.venv\Scripts\python.exe -m pytest` 執行。
2. 仍需先把 `backend` 放進 `PYTHONPATH`，因為測試使用 `app.*` 匯入。

### 9.3 驗收結果

驗收結果如下：

1. `backend/tests/test_portion_resolution.py`：`6 passed`
2. `backend/tests/test_analysis_draft.py`：`22 passed`
3. `backend/tests/test_food_mapping.py`：`7 passed`

判讀結論：P3-02 Backend MVP 已可接受。飲料單位換算與防呆已落地，confirm 主鏈未觀察到既有回歸，P3-01 canonical mapping 驗收也仍維持通過。

### 9.4 已驗收的 P3-02 行為

| 輸入 | 預期 nutrition_source | 預期結果 | 驗收狀況 |
| ---- | --------------------- | -------- | -------- |
| Black Coffee / black_coffee / bottle | drink_fallback | `375 g`、`drink_container_default`、`7.50 kcal` | 通過 |
| Tea Drink / tea_drink / can | drink_fallback | `330 g`、`drink_container_default`、`6.60 kcal` | 通過 |
| Black Tea / black_tea / 330 ml | drink_fallback | `330 g`、`direct_milliliters`、`6.60 kcal` | 通過 |
| Chicken Rice / grilled_chicken_rice / bowl | preset | `324 g`、`common_unit_conversion` | 通過 |
| Chicken Salad + Boiled Egg | preset | totals 仍為 `398.00 kcal / 34.50 protein / 23.30 fat / 12.60 carb` | 通過 |

### 9.5 目前邊界與後續待辦

本次完成的是 P3-02 的 Backend MVP，不代表整個 Priority 3 已完成。後續 P3-03 已在同日另行補上本地 `official_source` MVP；完整外部資料來源與更廣的甜飲精度仍需後續處理。

P3-02 驗收後仍需處理：

1. P3-03 已補上本地 `official_source` MVP；完整外部 nutrition source 與更廣資料來源仍待後續擴充
2. P3-04 metadata 與低噪音 UI 提示整合
3. P3-05 history / recommendation 對最終營養結果的穩定重用驗收
4. packaged drink 的甜飲精度與更多真實包裝標示樣本驗證

---

## 10. 2026-05-09 P3-03 nutrition source 層級驗收補充

本次補充驗收的目的，是確認 P3-03 已完成 MVP 版的三個核心面向：

1. 介面：建立 `NutritionResolutionInput` / `NutritionResolutionResult` 與 `resolve_item_nutrition()`
2. 流程控制：建立 `official_source -> canonical_mapping -> fallback_estimate -> special_guard` 的決策順序
3. 來源內容：建立本地策展版 `official_source` catalog

### 10.1 驗收範圍

本次驗收聚焦以下行為：

1. `official_source` 可以命中少量高信心食物。
2. 黑咖啡不再只依賴 `drink_fallback`，而是優先命中 `official_source`。
3. 白飯、水煮蛋可優先命中 `official_source`。
4. 茶飲未列入 official catalog 時，仍可走 `drink_fallback`。
5. 未知食物仍可走 `default_fallback`。
6. confirm API response 欄位維持不變。

### 10.2 驗收方式

本次實際執行的驗收命令如下：

```powershell
docker compose run --rm -e PYTHONPATH=/app backend pytest tests/test_nutrition_catalog.py tests/test_nutrition_resolution.py tests/test_analysis_draft.py -q
docker compose stop db
```

### 10.3 驗收結果

驗收結果如下：

1. `backend/tests/test_nutrition_catalog.py`：通過
2. `backend/tests/test_nutrition_resolution.py`：通過
3. `backend/tests/test_analysis_draft.py`：通過
4. 合計結果：`35 passed`

判讀結論：P3-03 nutrition source 層級已完成 MVP 版。系統已有最小可信 `official_source`，也保留 canonical mapping、fallback estimate 與 packaged drink 防呆。

### 10.4 已驗收的 source 行為

| 輸入 | 預期 nutrition_source | 預期結果 | 驗收狀況 |
| ---- | --------------------- | -------- | -------- |
| Black Coffee / black_coffee / bottle | official_source | 約 7.50 kcal | 通過 |
| White Rice / white_rice / bowl | official_source | 216.00 kcal | 通過 |
| Boiled Egg / boiled_egg / pcs | official_source | 78.00 kcal | 通過 |
| Tea Drink / tea_drink / ml | drink_fallback | 330 ml 約 6.60 kcal | 通過 |
| Mystery Food / mystery_food / bowl | default_fallback | 流程不中斷且 kcal 大於 0 | 通過 |

### 10.5 後續仍待 P3 收尾的項目

P3-03 已完成 MVP 版，但整個 Priority 3 若要正式標記完成，建議再補一輪 P3-04 / P3-05 收尾驗收：

1. 確認 `official_source`、`drink_fallback`、`default_fallback` 的 metadata 都能正確保存與回看。
2. 確認 history detail 能穩定重用 confirm 後的營養結果，而不是重新估算。
3. 確認 recommendation 使用的是完成時的 totals snapshot。

---

## 11. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. Priority 2： [Priority2-真實-AI-食物辨識與候選修正-v1.md](./Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md)
3. 手機實測紀錄： [Priority2-手機UX實測紀錄-v1.md](./Priority2-%E6%89%8B%E6%A9%9FUX%E5%AF%A6%E6%B8%AC%E7%B4%80%E9%8C%84-v1.md)
