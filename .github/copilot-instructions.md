# HappyMeal 專案指示 Project Instructions

## 文件規範與事實來源

- 若生成 Markdown 文件，內容與檔名請以正體中文為主，英文為輔。
- 需要保留英文時，優先使用「中文名稱 + English term」的寫法，避免全文以英文為主。
- 延續現有文件命名與版本方式，例如 `PRD-v1.md`、`System-Architecture-v1.md`。
- 只有平台或工具強制要求的固定檔名可維持英文，例如 `copilot-instructions.md`、`AGENTS.md`。
- 生成新文件時，若主題與既有文件高度重疊，優先更新原文件，而不是新增重複文件。

### 各文件職責

- 產品需求以 `docs/PRD-v1.md` 為主。
- 系統邊界、技術選型與模組切分以 `docs/System-Architecture-v1.md` 為主。
- 頁面資訊架構與使用流程以 `docs/IA-User-Flows-v1.md` 為主。
- 若需求未明確定義，優先提出與既有文件一致的方案，不要任意更換產品方向。

## 產品與體驗原則

- HappyMeal 是手機 Web 優先的營養與健身輔助服務。
- 介面預設應輕盈、低壓迫、資訊清楚，避免過度專業或過密排版。
- 每個畫面應聚焦單一主要任務，文案要短，優先使用卡片、數字摘要與清楚 CTA。
- 所有建議屬於 wellness guidance，不可寫成醫療診斷、治療或處方建議。

## 技術預設

- 前端：React + TypeScript + Vite，樣式以 Tailwind CSS + CSS Variables 為主。
- 後端：Python 3.12+、FastAPI、Pydantic v2，ORM 使用 SQLAlchemy 2.0 + Alembic。
- 資料庫：PostgreSQL。
- 前後端需維持清楚分離，第三方金鑰與敏感資料處理只放後端。
- 除非需求明確要求，否則不要自行改成 Next.js、React Native、Django 或單體架構。

## 資料與隱私約束

- 原始食物照片僅供分析暫存，分析完成後應刪除，不設計為長期保存。
- 身體數據、目標、歷史分析與同意紀錄視為敏感資料處理。
- LINE Login、AI API、營養資料來源 API 的整合與憑證管理必須由後端處理。

## 交付範圍

- 預設以 MVP 範圍交付，不主動擴張到社群、穿戴裝置、教練級規劃或後台 CMS。
- MVP 部署平台：後端 AWS Lightsail（Container Service + Database），前端 Vercel。詳細規劃見 `docs/部署與用量預估-v1.md`。
- 產品成長後可遷移至 ECS Fargate，遷移判斷與路徑見 `docs/setup/HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md`。

## 開發協作規範

- 當生成或修改的內容預期會進入版本控制時，請一併提供建議的 commit message。
- Commit message 格式採用 Conventional Commits：`type(scope): 說明`，說明以正體中文撰寫。
- 常用 type：`feat`、`fix`、`refactor`、`docs`、`chore`。
