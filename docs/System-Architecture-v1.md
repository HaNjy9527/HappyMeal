# HappyMeal System Architecture v1

## 1. 文件資訊

- 文件名稱：HappyMeal 系統架構文件
- 版本：v1
- 日期：2026-03-18
- 狀態：Draft
- 用途：定義第一版建議技術選型、系統模組、資料流與實作邊界

## 2. 架構目標

1. 支援手機 Web 優先的使用流程。
2. 降低第一版技術複雜度，保留後續擴充彈性。
3. 將第三方 AI API、登入與敏感資料處理集中在後端管理。
4. 明確分離前端、後端、資料庫與外部服務責任。

## 3. 推薦技術組合

### 3.1 前端

- React + TypeScript
- Vite
- React Router
- TanStack Query
- React Hook Form + Zod
- Tailwind CSS + CSS Variables

### 3.2 後端

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0
- Alembic

### 3.3 資料庫

- PostgreSQL

### 3.4 第三方服務

- LINE Login for OAuth
- AI Food Vision API for image recognition
- Nutrition data source API or curated nutrition mapping dataset

## 4. 為什麼這樣選

### 4.1 為什麼前端選 React + Vite

1. React 生態成熟，適合後續擴充多步驟表單、狀態管理與主題系統。
2. Vite 啟動快、結構輕，適合前後端分離專案。
3. 若日後需要 SEO 或內容頁強化，可再評估升級至 Next.js。

### 4.2 為什麼後端選 FastAPI

1. 產品核心是 API、OAuth、第三方 AI 串接與資料存取。
2. FastAPI 的文件與資料驗證能力適合快速定義清楚的 API 邊界。
3. 相比 Django，第一版不需要完整模板系統與重量級後台。

### 4.3 為什麼維持 PostgreSQL

1. 使用者、分析紀錄、建議快照、同意紀錄都很適合關聯式資料模型。
2. 後續可加入 JSON 欄位承接彈性結構，如 AI 原始回應摘要。

## 5. 邏輯架構

### 5.1 前端責任

1. 呈現頁面與主題風格。
2. 管理登入狀態與使用者互動流程。
3. 處理拍照、圖片上傳、表單驗證、結果展示。
4. 不直接持有第三方服務金鑰。

### 5.2 後端責任

1. 處理 LINE Login OAuth callback 與會員建立。
2. 接收圖片、執行 AI 食物辨識流程。
3. 對應營養資料並計算總營養素。
4. 根據使用者身體資料與目標產生建議。
5. 寫入歷史紀錄與同意紀錄。
6. 管理所有敏感資料與第三方 API 存取。

### 5.3 資料庫責任

1. 保存會員資料與個人檔案。
2. 保存歷史分析摘要與建議快照。
3. 保存熱門運動資料與同意紀錄。
4. 不保存原始食物照片。

## 6. 高層資料流

### 6.1 登入流程

1. 前端導向 LINE Login。
2. 使用者完成授權後回到後端 callback。
3. 後端驗證 token 並建立或更新會員資料。
4. 後端建立 session。
5. 前端取得登入狀態與基本會員資訊。

### 6.2 食物分析流程

1. 使用者於前端拍照或上傳圖片。
2. 前端將圖片送往後端分析 API。
3. 後端暫存圖片供分析使用。
4. 後端呼叫 AI 辨識服務取得候選食物結果。
5. 後端將候選結果轉為可供前端確認的標準格式。
6. 前端顯示候選食物與份量輸入。
7. 使用者確認後送出修正結果。
8. 後端查詢營養資料來源並計算總營養素。
9. 後端依據使用者 profile 產出建議與推薦運動。
10. 後端保存分析摘要與建議快照。
11. 後端刪除暫存原始圖片。
12. 前端顯示最終結果。

### 6.3 歷史查詢流程

1. 前端請求歷史列表。
2. 後端回傳分析摘要與建議快照。
3. 前端以卡片列表呈現歷史結果。

## 7. 模組切分

### 7.1 前端模組

1. Auth Module
2. Profile Module
3. Analysis Module
4. History Module
5. Exercise Module
6. Theme Module
7. Consent Module

### 7.2 後端模組

1. Auth Router and Service
2. User Profile Router and Service
3. Analysis Router and Service
4. Nutrition Mapping Service
5. Recommendation Service
6. Exercise Service
7. Consent Service

## 8. 資料模型基線

### 8.1 User

- id
- line_user_id
- display_name
- avatar_url
- theme_preference
- created_at
- updated_at

### 8.2 UserProfile

- user_id
- age
- height_cm
- weight_kg
- activity_level
- goal_type
- goal_weight_kg
- updated_at

### 8.3 FoodAnalysis

- id
- user_id
- analyzed_at
- status
- total_kcal
- total_protein_g
- total_fat_g
- total_carb_g
- guidance_snapshot_json

### 8.4 FoodAnalysisItem

- id
- analysis_id
- food_name
- normalized_food_name
- portion_value
- portion_unit
- confidence_score
- kcal
- protein_g
- fat_g
- carb_g

### 8.5 ExerciseCatalog

- id
- name
- category
- met_value
- display_order
- is_popular

### 8.6 RecommendationSnapshot

- id
- analysis_id
- target_calories_kcal
- target_protein_g
- target_fat_g
- target_carb_g
- recommended_exercises_json
- generated_at

### 8.7 ConsentRecord

- id
- user_id
- consent_type
- policy_version
- accepted_at

## 9. API 邊界建議

### 9.1 Auth APIs

- GET /auth/line/login
- GET /auth/line/callback
- GET /auth/me
- POST /auth/logout

### 9.2 Profile APIs

- GET /profile
- PUT /profile
- PUT /profile/theme

### 9.3 Analysis APIs

- POST /analyses
- POST /analyses/{id}/image
- POST /analyses/{id}/confirm
- GET /analyses/{id}
- GET /analyses

### 9.4 Exercise APIs

- GET /exercises/popular
- GET /exercises/estimate

### 9.5 Consent APIs

- GET /consents/current
- POST /consents

## 10. 推薦計算邏輯邊界

1. 第一版只提供一般健康管理用途的估算與建議。
2. 使用者目標分為增肌或減脂兩種主路徑。
3. 活動量使用簡化等級，不在第一版採用極細緻計算模型。
4. 對於熱量赤字與盈餘需設置安全上限與下限。
5. 推薦內容需為簡短、可行的建議，不生成長篇內容。

## 11. 安全與隱私設計

1. 原始照片僅作短暫分析暫存，完成後刪除。
2. 所有第三方 API 金鑰僅配置於後端環境變數。
3. 身體資料、目標、歷史分析資料需視為敏感個資保護。
4. 必須有隱私政策版本與同意紀錄。
5. 建議使用安全 cookie 管理 session。

## 12. 部署建議

### 12.1 第一版建議

- Frontend: Vercel or equivalent static hosting
- Backend: Render, Railway, or equivalent managed Python hosting
- Database: Managed PostgreSQL

### 12.2 不建議第一版先做

1. K8s
2. 複雜微服務拆分
3. 自建圖片儲存與 CDN 基礎設施
4. 高複雜度 event-driven architecture

## 13. 架構風險

1. AI 辨識服務對亞洲複合餐點辨識可能不穩定。
2. 若完全依賴單一 AI 供應商，成本與品質風險較高。
3. 若未保留手動修正入口，整體使用體驗會直接失敗。
4. 若第一版導入太多即時互動與動畫，手機效能與舒適度會受影響。

## 14. 後續技術擴充方向

1. 引入手動食物搜尋與自訂食物庫。
2. 引入每日累積熱量與營養素追蹤。
3. 引入多登入方式。
4. 視需求追加管理後台。
5. 根據資料量與成本，再決定是否加入快取層或背景工作佇列。
