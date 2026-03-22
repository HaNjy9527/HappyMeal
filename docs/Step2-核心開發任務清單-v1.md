# Step 2 核心開發任務清單 v1

- 文件名稱：Step 2 核心開發任務清單
- 版本：v1
- 日期：2026-03-20
- 狀態：Draft
- 用途：將 HappyMeal Step 2 細拆為可排進 sprint 的工作包、ticket 與驗收標準，並明確鎖定本階段邊界

---

## 1. 文件定位

本文件只處理 [HappyMeal 開發起點指引](HappyMeal_Dev_Kickoff.md) 中的 Step 2｜開發程式。

本文件不是 [PRD-v1.md](PRD-v1.md) 第 16 節的 Phase 2 候選功能清單。

為避免名稱混淆，後續實作、排票與討論請統一使用「Step 2 核心開發」，不要把本文件內容稱為 Phase 2。

---

## 2. 範圍

### 2.1 納入範圍

Step 2 的目標是在本地 Docker 環境內，把 MVP 主流程開發到可驗證的程度。

包含：

1. 核心資料模型
2. 第一版正式 migration
3. 最小 seed 資料
4. profile 與 consent 能力
5. analysis draft、候選確認、confirm 主流程
6. history list 與 history detail
7. 前端最小主流程串接
8. backend 基本測試與手動驗收

### 2.2 明確排除範圍

本文件不處理以下內容：

1. GitHub Actions CI
2. GitHub Actions CD
3. AWS、ECR、RDS、ECS、正式部署
4. 正式雲端圖片儲存
5. 手動搜尋完整食物資料庫
6. 每日飲食累積紀錄
7. 更多主題模式與無障礙優化
8. 付費方案與進階報表
9. 社群、分享、排行榜
10. 穿戴裝置串接
11. 後台 CMS
12. 教練級規劃、逐餐菜單、週期化課表

### 2.3 範圍守門規則

若新需求符合以下任一條件，視為超出 Step 2：

1. 需要新增新的主要使用流程，而不是補齊既有流程
2. 需要新增新的平台能力，例如部署、CI/CD、雲端基礎設施
3. 需要把單次分析延伸成長期追蹤、報表或商業化模組
4. 需要讓資料模型額外承接未列於 MVP 的產品面向

---

## 3. 本階段完成定義

Step 2 完成，不代表產品全部完成。

Step 2 的完成標準只有以下幾項：

1. 本地 Docker 環境可執行 migration 與最小 seed
2. 使用者可完成 profile 建檔與 consent 保存
3. 使用者可完成一次 analysis 主流程
4. 系統可保存並查詢歷史摘要與單筆詳情
5. 前端可串起最小主流程頁面
6. backend 有基本測試覆蓋關鍵主鏈

---

## 4. 核心資料模型基線

第一批核心模型至少包含以下 7 個：

1. User
2. UserProfile
3. FoodAnalysis
4. FoodAnalysisItem
5. RecommendationSnapshot
6. ExerciseCatalog
7. ConsentRecord

建議在 Step 2 一開始就定死以下 enum，避免後續反覆修改 schema：

1. analysis_status
2. activity_level
3. goal_type
4. theme_preference
5. consent_type

---

## 5. 工作包拆解

### WP-01 資料模型與 enum 基線

目標：把 Step 2 所需的資料結構一次定到能支撐 profile、analysis、history、recommendation、consent。

包含：

1. 七張核心表的欄位、型別、nullable 規則
2. 外鍵、索引、unique constraint
3. created_at、updated_at 等共通欄位策略
4. enum 清單與值域

不包含：

1. 每日累積紀錄資料表
2. 完整手動食物資料庫模型
3. 付費與報表相關資料表

完成定義：

1. API 欄位與前端型別不需要再為 history 或 recommendation 回頭翻修 schema
2. 所有核心流程都可對應到明確資料表與欄位

### WP-02 初始業務 migration

目標：把 Step 1 的 Alembic 骨架推進到第一版正式 schema。

包含：

1. 建立七張核心表
2. 建立外鍵、索引、unique constraint
3. 決定 ExerciseCatalog 使用 migration seed 或獨立 seed script

不包含：

1. 正式雲端 migration 流程
2. 大量初始化資料匯入

完成定義：

1. Docker 內可 upgrade 到最新版本
2. 新資料庫可成功建立所有核心表

### WP-03 共用資料存取與後端基礎

目標：讓後續 router、service 與測試共用同一套 DB 存取基礎。

包含：

1. session factory
2. FastAPI dependency
3. 設定注入與最小錯誤處理策略
4. 測試可重用的 DB 基礎

不包含：

1. sync 與 async 雙軌並行
2. 過度抽象的 repository framework

完成定義：

1. route 可以穩定取得 DB session
2. 測試不需要為每個模組各自重建連線方式

### WP-04 Profile 與 Consent 能力

目標：打通首次建檔與後續更新。

包含：

1. User 基本資料取得或建立策略
2. UserProfile 建立與更新
3. theme_preference 保存
4. ConsentRecord 保存與版本欄位策略

不包含：

1. 多登入方式管理
2. 帳號中心與安全設定頁

完成定義：

1. profile 可成功讀取與更新
2. consent 與 theme 偏好可持久化

### WP-05 Analysis 建立與候選流程

目標：先打通分析流程前半段，讓前端可進入 Candidate Confirmation。

包含：

1. 建立 analysis draft
2. 接圖片上傳或 mock candidate
3. 保存分析狀態
4. 定義候選食物回傳格式

不包含：

1. 多 AI provider 切換
2. 正式圖片儲存方案

完成定義：

1. 前端可以取得候選食物清單與分析狀態
2. analysis 可從 draft 進入待確認狀態

### WP-06 Analysis 確認、營養估算與建議

目標：完成 analysis 主鏈最核心的結果產生。

包含：

1. 寫入 FoodAnalysisItem
2. 計算總熱量與三大營養素
3. 依 UserProfile 與 ExerciseCatalog 生成簡短建議
4. 保存 RecommendationSnapshot
5. 更新 analysis totals 與完成狀態

不包含：

1. 高精度醫療或專業營養建議
2. 週計畫、逐餐菜單、教練級規劃

完成定義：

1. analysis 可從待確認進入 completed
2. 結果資料可被 history 直接重用

### WP-07 History 列表與明細

目標：把已保存的 analysis 結果轉成可查詢、可呈現的歷史能力。

包含：

1. 歷史列表摘要欄位
2. 單筆詳情欄位
3. 日期排序與基本查詢
4. 建議快照回傳

不包含：

1. 搜尋全文
2. 進階篩選與統計圖表

完成定義：

1. 使用者可從 history list 進入 history detail
2. 不顯示原始食物圖片

### WP-08 前端最小主流程串接

目標：只串最小可驗證頁面，不擴張資訊架構。

包含：

1. Profile Edit
2. Start Analysis
3. Candidate Confirmation
4. Analysis Result
5. History List
6. History Detail

不包含：

1. Landing 精修
2. Home Dashboard 完整體驗
3. 額外主題模式細化

完成定義：

1. 使用者可從建檔一路走到單次分析完成並回看歷史

### WP-09 測試與驗收

目標：把 Step 2 做成可驗證，而不是只靠人工印象判斷。

包含：

1. backend 至少覆蓋 profile、analysis confirm、history detail
2. migration 與 seed 執行驗證
3. API docs 驗證
4. 前端主流程手動驗證

不包含：

1. 完整雲端部署驗收
2. 完整 E2E 平台建置

完成定義：

1. 本地 Docker 內可完成 migration、seed、API 測試與主流程驗證

---

## 6. 依賴順序

1. 先做 WP-01，否則 schema、API、前端型別會反覆變動
2. 再做 WP-02 與 WP-03，先把資料庫與後端基礎打穩
3. WP-04 要早於 WP-06，因為 recommendation 依賴 profile
4. WP-05 與 WP-06 構成 analysis 主鏈，必須連續完成
5. WP-07 在 WP-06 的資料寫入結構穩定後進行
6. WP-08 依賴對應 API 基本完成
7. WP-09 最後收尾，但測試樣板應在 WP-04 起同步準備

---

## 7. Sprint 建議

### Sprint 1｜資料與建檔基線

範圍：WP-01、WP-02、WP-03、WP-04

目標：

1. 資料表、migration、session、profile、consent 打通
2. 建立後續 analysis 主鏈的穩定基底

里程碑：

1. 使用者可完成建檔，資料可持久化

### Sprint 2｜分析與歷史主鏈

範圍：WP-05、WP-06、WP-07

目標：

1. analysis draft、候選確認、confirm、history 打通

里程碑：

1. 可完成一次分析並在歷史中回看

### Sprint 3｜前端整合與驗收

範圍：WP-08、WP-09

目標：

1. 前後端主流程可驗證
2. 補測試與手動驗收收尾

里程碑：

1. 從 Profile Edit 到 History Detail 的最小 MVP 流程可操作

---

## 8. Ticket 清單

### 8.1 Backend Backlog

| ID    | 任務                                                | 依賴                       | 驗收條件                                            | 明確不做                 |
| ----- | --------------------------------------------------- | -------------------------- | --------------------------------------------------- | ------------------------ |
| BE-01 | 定義核心 enum 與欄位規格                            | 無                         | 七張核心表的欄位、enum、nullable 規則與索引需求定稿 | 每日累積、支付、報表欄位 |
| BE-02 | 設計七張核心表關聯與 constraint                     | BE-01                      | 各表外鍵、unique constraint、刪除策略可明確對應流程 | 額外延伸表               |
| BE-03 | 建立第一版業務 migration                            | BE-01, BE-02               | 新資料庫可成功 upgrade 並建立核心表                 | 雲端 migration 流程      |
| BE-04 | 建立 ExerciseCatalog seed 策略與最小資料集          | BE-03                      | 至少 20 種常見運動可寫入資料庫                      | 進階內容管理工具         |
| BE-05 | 補 FastAPI DB dependency 與 session 管理            | BE-03                      | route 與測試可共用同一套 DB session 方式            | sync 與 async 雙軌       |
| BE-06 | 建立 User 與 UserProfile schema、service、validator | BE-05                      | profile 相關資料結構、驗證規則與 service 邊界定稿   | 帳號中心                 |
| BE-07 | 實作 GET profile                                    | BE-06                      | 可回傳目前使用者 profile 與 theme 狀態              | 複雜權限系統             |
| BE-08 | 實作 PUT profile                                    | BE-06                      | 可更新 age、height、weight、activity、goal 等欄位   | 進階目標規劃             |
| BE-09 | 實作 theme preference 更新                          | BE-06                      | 可保存並重新讀回 theme_preference                   | 多主題系統擴張           |
| BE-10 | 實作 consent record 寫入與查詢                      | BE-05, BE-06               | 可保存 consent_type、policy_version、accepted_at    | 法務後台                 |
| BE-11 | 建立 analysis draft API                             | BE-05                      | 可建立 draft analysis 並回傳 id 與初始狀態          | 每日累積紀錄             |
| BE-12 | 建立 image upload 或 mock candidate 流程            | BE-11                      | 可接收圖片或 mock 輸入並產生候選資料                | 正式雲端圖片儲存         |
| BE-13 | 定義 candidate response 格式                        | BE-11, BE-12               | 候選食物、信心分數、份量欄位格式固定                | 搜尋型食物資料庫         |
| BE-14 | 實作 analysis confirm 寫入 item                     | BE-13                      | 可將使用者確認結果寫入 FoodAnalysisItem             | 逐餐規劃                 |
| BE-15 | 實作營養 totals 計算                                | BE-14                      | 產出 total_kcal、protein、fat、carb 並回寫 analysis | 進階營養學模型           |
| BE-16 | 實作 recommendation 生成規則                        | BE-04, BE-08, BE-15        | 可依 profile 與運動資料回傳簡短建議與推薦運動       | 醫療建議、週計畫         |
| BE-17 | 寫入 recommendation snapshot                        | BE-16                      | RecommendationSnapshot 可與 analysis 綁定保存       | 報表與趨勢分析           |
| BE-18 | 實作 history list API                               | BE-17                      | 可回傳日期、食物摘要、總熱量、建議摘要              | 進階搜尋與篩選           |
| BE-19 | 實作 history detail API                             | BE-17                      | 可回傳單次分析摘要、食物明細、營養結果、建議快照    | 原始圖片展示             |
| BE-20 | 補 profile API 測試                                 | BE-07, BE-08, BE-09, BE-10 | profile 與 consent 關鍵案例有自動化測試             | 完整 E2E                 |
| BE-21 | 補 analysis confirm 測試                            | BE-14, BE-15, BE-16, BE-17 | confirm 主鏈關鍵案例有自動化測試                    | 第三方 provider 壓測     |
| BE-22 | 補 history detail 測試                              | BE-18, BE-19               | 歷史列表與明細查詢有自動化測試                      | 跨期統計測試             |

### 8.2 Frontend Backlog

| ID    | 任務                                 | 依賴                                     | 驗收條件                                                | 明確不做             |
| ----- | ------------------------------------ | ---------------------------------------- | ------------------------------------------------------- | -------------------- |
| FE-01 | 建立 profile form 與資料讀寫         | BE-07, BE-08, BE-09, BE-10               | Profile Edit 可讀取與更新資料，並處理基本驗證與儲存狀態 | 進階個人設定頁       |
| FE-02 | 串 Start Analysis 上傳入口           | BE-11, BE-12                             | 使用者可從前端建立 analysis 並送出圖片或 mock 輸入      | 相機體驗最佳化       |
| FE-03 | 串 Candidate Confirmation 編輯與送出 | BE-13, BE-14                             | 可編輯候選食物與份量，並送出 confirm                    | 手動食物搜尋資料庫   |
| FE-04 | 串 Analysis Result 顯示摘要與建議    | BE-15, BE-16, BE-17                      | 顯示總熱量、三大營養素、食物明細與推薦運動              | 報表視覺化           |
| FE-05 | 串 History List                      | BE-18                                    | 可顯示日期、食物摘要、總熱量、建議摘要列表              | 進階篩選器           |
| FE-06 | 串 History Detail                    | BE-19                                    | 可查看單筆分析詳情與建議快照                            | 圖片回放             |
| FE-07 | 處理 loading、error、empty state     | FE-01, FE-02, FE-03, FE-04, FE-05, FE-06 | 六個主流程頁面都有最小狀態處理                          | 動畫精修、多主題細化 |

### 8.3 QA 與驗收 Backlog

| ID    | 任務                             | 依賴                | 驗收條件                                                      | 明確不做            |
| ----- | -------------------------------- | ------------------- | ------------------------------------------------------------- | ------------------- |
| QA-01 | 驗證 Docker 內 migration 與 seed | BE-03, BE-04        | 新環境可成功建立資料表與最小運動資料                          | 雲端部署驗收        |
| QA-02 | 驗證 API docs 可用               | BE-07 至 BE-19      | FastAPI docs 可看到 Step 2 核心 API                           | 對外公開 API portal |
| QA-03 | 驗證主流程手動跑通一次           | FE-01 至 FE-07      | 從 Profile Edit 到 Analysis Result 再到 History Detail 可操作 | 壓力測試            |
| QA-04 | 驗證原始圖片未被長期保存         | BE-12, BE-17        | 分析完成後不依賴永久保存原圖                                  | 正式物件儲存方案    |
| QA-05 | 驗證免責聲明與 consent 流程存在  | BE-10, FE-01, FE-04 | profile 或相關流程可看到必要 consent 與非醫療用途提醒         | 法務營運後台        |

---

## 9. 驗證矩陣

本章的用途不是重複 backlog，而是把「完成後要怎麼證明有做到」與「怎麼證明沒有超出範圍」固定下來。

建議每次 sprint 結束都更新一次狀態欄，狀態只使用以下三種：

1. `Not Started`
2. `In Progress`
3. `Done`

### 9.1 核心完成驗證矩陣

| 驗證面向                | 對應工作包 / Ticket          | 驗證重點                                                                                   | 建議證據                                                                                                                                                             | 狀態 |
| ----------------------- | ---------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| 資料模型基線            | WP-01, BE-01, BE-02          | 七張核心表、五個 enum、FK、index、unique constraint 已定稿，且不含每日累積、支付、報表欄位 | model 檔案、migration diff、schema review 紀錄                                                                                                                       | Done |
| 初始 migration          | WP-02, BE-03                 | 新資料庫可成功 upgrade 到最新版本並建立所有核心表                                          | Docker 內 `alembic upgrade head` 成功輸出                                                                                                                            | Done |
| ExerciseCatalog seed    | WP-02, BE-04, QA-01          | 最少 20 筆常見運動成功寫入，seed 可重跑                                                    | seed script、資料列數查詢結果                                                                                                                                        | Done |
| 共用 DB 存取            | WP-03, BE-05                 | route 與測試共用同一套 session factory 與 FastAPI dependency                               | session module、pytest fixture、API smoke test                                                                                                                       | Done |
| Profile 讀取            | WP-04, BE-06, BE-07          | 可回傳目前使用者 profile 與 theme 狀態                                                     | `GET /profile` response、API test                                                                                                                                    | Done |
| Profile 更新            | WP-04, BE-08                 | 可更新 age、height、weight、activity、goal 等欄位，且驗證規則生效                          | `PUT /profile` response、validator test                                                                                                                              | Done |
| Theme preference        | WP-04, BE-09                 | theme_preference 可保存並重新讀回                                                          | `PUT /profile/theme` response、重新查詢結果                                                                                                                          | Done |
| Consent 保存與查詢      | WP-04, BE-10, QA-05          | consent_type、policy_version、accepted_at 可保存且查詢得到                                 | `POST /consents`、`GET /consents/current` response、API test                                                                                                         | Done |
| Analysis draft          | WP-05, BE-11                 | 可建立 draft analysis 並回傳 id 與初始狀態                                                 | `POST /analyses` response、API test                                                                                                                                  | Done |
| 圖片上傳與 candidate    | WP-05, BE-12, BE-13          | 可接收圖片並回傳固定 candidate 格式；本階段允許 mock candidate                             | 上傳 API response、candidate schema、手動流程截圖                                                                                                                    | Done |
| Analysis confirm        | WP-06, BE-14                 | 可將使用者確認結果寫入 FoodAnalysisItem                                                    | `POST /analyses/{id}/confirm` response、DB query、API test                                                                                                           | Done |
| 營養 totals 計算        | WP-06, BE-15                 | total_kcal、protein、fat、carb 已正確回寫 analysis                                         | confirm test、analysis DB row、result API response                                                                                                                   | Done |
| Recommendation 生成     | WP-06, BE-16                 | 可依 profile 與運動資料生成簡短建議與推薦運動，且語氣不越界到醫療建議                      | recommendation service test、result response                                                                                                                         | Done |
| Recommendation snapshot | WP-06, BE-17                 | RecommendationSnapshot 已與 analysis 綁定保存，供後續 history 重用                         | DB query、history/detail response                                                                                                                                    | Done |
| History list            | WP-07, BE-18                 | 可回傳日期、食物摘要、總熱量、建議摘要                                                     | `GET /analyses` response、API test                                                                                                                                   | Done |
| History detail          | WP-07, BE-19, BE-22          | 可回傳單次分析摘要、食物明細、營養結果、建議快照，且不回原始圖片                           | `GET /analyses/{id}` response、API test                                                                                                                              | Done |
| 前端最小主流程          | WP-08, FE-01 至 FE-07, QA-03 | 可從 Profile Edit 一路走到 History Detail，且六頁都有 loading、error、empty state          | 2026-03-22 瀏覽器手動驗收：Profile → Start Analysis → Candidate Confirmation → Analysis Result → History List → History Detail；network 全數 2xx、console 無前端錯誤 | Done |
| Backend 測試覆蓋        | WP-09, BE-20, BE-21, BE-22   | profile、analysis confirm、history detail 關鍵案例皆有自動化測試                           | pytest 結果、測試檔案列表                                                                                                                                            | Done |
| API docs 驗證           | WP-09, QA-02                 | `/docs` 可看到 Step 2 核心 API                                                             | 2026-03-22 Swagger UI 驗證：/profile、/profile/theme、/consents、/analyses、/analyses/{analysis_id}/image、/analyses/{analysis_id}/confirm、/analyses/{analysis_id}  | Done |
| 圖片刪除驗證            | WP-09, QA-04                 | analysis 完成後不依賴永久保存原圖                                                          | 暫存目錄檢查結果、history/detail response 不含圖片欄位                                                                                                               | Done |

### 9.2 範圍守門驗證矩陣

這一張表只檢查「有沒有超做」。只要任一列出現 `Yes`，就必須在 sprint review 時註記為超出 Step 2，不能直接算進完成定義。

| 範圍守門問題                                             | 允許答案 | 檢查方式                                       | 結果 |
| -------------------------------------------------------- | -------- | ---------------------------------------------- | ---- |
| 是否新增 Step 2 文件未列出的主要使用流程                 | No       | 對照 IA、PRD 與本文件第 5 節                   | No   |
| 是否新增新的平台能力，例如 CI/CD、正式部署、雲端基礎設施 | No       | 檢查 repo、infra 變更、部署腳本                | No   |
| 是否新增每日飲食累積、報表、商業化、社群、CMS 等延伸模組 | No       | 檢查資料表、API、前端頁面清單                  | No   |
| 是否把 LINE Login 一起納入 Step 2 核心完成定義           | No       | 檢查 auth router、OAuth callback、前端登入流程 | No   |
| 是否導入正式雲端圖片儲存                                 | No       | 檢查 storage service、雲端憑證、圖片 URL 欄位  | No   |
| 是否做了手動搜尋完整食物資料庫                           | No       | 檢查 food search API、前端搜尋畫面             | No   |
| 是否新增超出 MVP 的主題模式或完整無障礙重構              | No       | 檢查 theme 數量、前端設計 scope                | No   |
| 是否新增支付、方案、後台管理能力                         | No       | 檢查 schema、API、頁面、第三方整合             | No   |

### 9.3 結案時的最終核對方式

Step 2 結案前，請依以下順序核對：

1. 先更新 9.1 的狀態欄，確認所有 Step 2 必要項目已達 `Done`。
2. 再更新 9.2 的結果欄，確認所有超範圍檢查仍為 `No`。
3. 若 9.1 有未完成項目，或 9.2 有任一列不是 `No`，不得宣告 Step 2 完成。
4. 若有額外做的工作，但不影響 Step 2 邊界，需在 release note 或 sprint note 中單列為「額外工作」，不要混入完成定義。

---

## 10. 排票原則

後續若要把 ticket 正式建到 sprint board，建議每張票固定包含以下欄位：

1. 目的
2. 範圍
3. 明確不做
4. 驗收條件
5. 依賴項目

若無法清楚寫出「明確不做」，代表該 ticket 還沒有收斂好，暫時不應進 sprint。

---

## 11. 變更控制

若要新增需求，請先回答以下問題：

1. 它是否直接支撐 Profile、Analysis、History、Consent 其中一條既有主鏈。
2. 它是否為 Step 2 驗收條件所必需，而不是體驗加分項。
3. 它是否會導致新增主要資料表、主要頁面或外部平台能力。

若第 1 題為否，或第 3 題為是，原則上應移出 Step 2。

---

## 12. 對應文件

1. 產品需求與 MVP 邊界： [PRD-v1.md](PRD-v1.md)
2. 系統模組、資料模型、API 基線： [System-Architecture-v1.md](System-Architecture-v1.md)
3. 頁面與流程： [IA-User-Flows-v1.md](IA-User-Flows-v1.md)
4. 開發順序總覽： [HappyMeal_Dev_Kickoff.md](HappyMeal_Dev_Kickoff.md)
