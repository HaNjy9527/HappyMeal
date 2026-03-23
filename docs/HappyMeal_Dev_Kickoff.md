# HappyMeal Dev Kickoff

- 文件名稱：HappyMeal 開發起點指引
- 版本：v1
- 日期：2026-03-19
- 狀態：Draft
- 用途：定義第一版實作的正確起點順序、每步驗收條件與常見卡關提醒

---

## 為什麼需要這份文件

規劃文件（PRD、IA、Architecture）定義的是「做什麼」與「怎麼設計」。
這份文件定義的是「從哪裡開始動手」，以及「怎麼確認每步做完了」。

核心原則：**本地先跑通，再往外推。**
不要在 app 還沒寫完、Docker 也沒測過的情況下就去設定 AWS，
那樣出問題時你不知道錯在哪一層。

---

## 實作優先順序

```
Step 1：Docker 本地環境
        │
        ▼
Step 2：開發程式（本地 Docker 內開發）
        │
        ├──────────────────────┐
        ▼                      ▼
Step 3：GitHub Actions CI     Step 4：AWS 設定
        │                      │
        └──────────┬───────────┘
                   ▼
           Step 5：GitHub Actions CD（串接部署）
```

Step 3 和 Step 4 可以平行推進，互不相依。
Step 5 需要 Step 3 和 Step 4 都完成才能串接。

---

## Step 1｜Docker 本地環境

### 目標

讓整個專案可以用一行指令在任何機器上跑起來，不依賴本機安裝的 Python 版本或 PostgreSQL。

### 要做的事

- [ ] 寫 `backend/Dockerfile`（以 `python:3.12-slim` 為基底）
- [ ] 寫 `frontend/Dockerfile`（multi-stage build，nginx 提供靜態檔）
- [ ] 寫根目錄的 `docker-compose.yml`（核心服務）
- [ ] 寫根目錄的 `docker-compose.override.yml`（本地開發覆寫）
- [ ] 建立 `.env.example`（列出所有需要的環境變數，值留空）
- [ ] 建立 `.env`（填入本地開發用的真實值，加入 `.gitignore`）
- [ ] 初始化 Alembic 骨架（只做設定與目錄，不做正式 migration）

### 驗收條件

```bash
docker compose up
```

執行後：

- `http://localhost:8000/docs` 能開（FastAPI 自動產生的 API 文件）
- `http://localhost:5173` 能開（React 前端）
- PostgreSQL container 正常啟動，backend 能連到 db

### 對應文件

Step 1 實作細節 → `Step1-Docker-本地開發實作指南-v1.md`

### 常見卡關

- `.env` 裡的 `DATABASE_URL` 主機名稱要用 `db`（docker-compose service 名稱），不是 `localhost`
- `depends_on` 只確保 container 啟動順序，不確保 PostgreSQL 已 ready，第一次啟動可能需要稍等幾秒
- frontend container 熱更新需要掛 volume，記得在 docker-compose 裡設定 `volumes`

---

## Step 2｜開發程式

### 目標

在 Docker 環境內把核心功能開發到可以跑 API 測試的程度，不是等全部功能完成才進下一步。

### 範圍邊界

本節的 Step 2 是「核心產品開發階段」，不是 [PRD-v1.md](PRD-v1.md) 第 16 節的 Phase 2 候選功能。

為避免 scope 漂移，Step 2 只聚焦：

1. 資料模型、migration、seed
2. profile、consent、analysis、history 主流程
3. 前端最小主流程串接
4. backend 基本測試與本地驗收

Step 2 不包含：

1. GitHub Actions
2. AWS 與正式部署
3. 正式雲端圖片儲存
4. 手動搜尋完整食物資料庫
5. 每日飲食累積紀錄
6. 更多主題模式、無障礙優化
7. 付費方案、進階報表、後台 CMS

### Step 2 細化文件

Step 2 的工作包、sprint、backend backlog、frontend backlog 與 QA 驗收清單，統一以 [Step2-核心開發任務清單-v1.md](Step2-核心開發任務清單-v1.md) 為準。

### 建議起點順序（後端）

- [ ] FastAPI 主程式骨架（`main.py`，含基本 health check route）
- [ ] SQLAlchemy 資料模型（User、UserProfile、FoodAnalysis 先建）
- [ ] 建立第一個業務 migration（延續 Step 1 的 Alembic 骨架）
- [ ] LINE Login OAuth 流程（`/auth/line/login`、`/auth/line/callback`）
- [ ] Profile API（`GET /profile`、`PUT /profile`）
- [ ] 圖片上傳與 AI 辨識流程（`POST /analyses`、`POST /analyses/{id}/image`）
- [ ] 營養估算與建議生成（`POST /analyses/{id}/confirm`）

### 建議起點順序（前端）

- [ ] Vite + React + TypeScript 專案初始化
- [ ] React Router 路由設定（Landing、Home、Analysis、History、Profile）
- [ ] TanStack Query 設定（API client）
- [ ] LINE Login 串接
- [ ] 各頁面依 IA 文件逐步實作

### 驗收條件

- 可以用 `curl` 或 FastAPI `/docs` 打通至少一個完整流程（登入 → 上傳圖片 → 取得分析結果）
- pytest 有基本測試覆蓋（至少 auth 和 analysis 主流程）

### 對應文件

- API 設計 → `Architecture_v1`（Section 9）
- 資料模型 → `Architecture_v1`（Section 8）
- 頁面與流程 → `IA_and_User_Flows_v1`（Section 6）

### 常見卡關

- LINE Login callback URL 在 LINE Developers Console 必須事先設定，本地開發可用 `ngrok` 暫時代理
- AI 食物辨識 API 金鑰只放在後端 `.env`，前端不可直接呼叫
- Alembic migration 要在 container 內執行，不是在本機直接跑

---

## Step 3｜GitHub Actions CI

### 目標

每次 push 或開 PR 時，自動跑測試並 build Docker image，確保主線不壞掉。

### Step 3 細化文件

Step 3 的工作包、ticket、驗收矩陣與範圍守門，統一以 [Step3-GitHub-Actions-CI-實作指南-v1.md](Step3-GitHub-Actions-CI-實作指南-v1.md) 為準。

### 要做的事

- [ ] 建立 `.github/workflows/ci.yml`
- [ ] 設定 `backend-test` job（執行 pytest，沿用現有 SQLite 測試 fixture）
- [ ] 設定 `frontend-build` job（執行 `npm run build`）
- [ ] 設定 `docker-build` job（驗證 backend 與 frontend Docker image 可成功 build）
- [ ] 設定 Branch Protection Rule；若目前 GitHub private repo 方案不支援 enforcement，需記錄平台限制並以人工流程替代

### 驗收條件

- 開一個 PR，GitHub Actions 自動跑起來
- pytest 全過，Actions 顯示綠色
- 故意讓一個測試失敗，確認 Actions 顯示紅燈
- 若 GitHub 方案支援 branch protection enforcement，確認紅燈 PR 無法 merge

### 對應文件

完整 workflow 範例與背景說明 → `HappyMeal_AWS_Docker_CICD.md` Part 3

### 常見卡關

- 以為 CI 一定要接 PostgreSQL，但目前 backend 測試實作其實使用 SQLite in-memory fixture
- `working-directory` 要設定正確，否則 `pip install`、`pytest` 與 `npm run build` 會找不到路徑
- 本機能過不代表 Docker image 一定能 build，docker-build job 不能省略
- private repo 在目前 GitHub 方案下可能顯示 branch protection `Not enforced`，此時規則不會真的阻止 merge

---

## Step 4｜AWS 設定

### 目標

把 AWS 基礎設施建好，讓 Step 5 的 CD 有地方可以部署。

### 要做的事

- [ ] 建立 AWS 帳號，開啟 Free Tier
- [ ] 建立專用 IAM user（給 GitHub Actions 用），只給最小必要權限
- [ ] 建立 ECR repository（`happymeal-backend`）
- [ ] 建立 RDS PostgreSQL（`db.t3.micro`，放在 private subnet）
- [ ] 建立 ECS Cluster + Task Definition + Service（Fargate）
- [ ] 設定 S3 bucket（`happymeal-temp`，加 Lifecycle Policy 1 小時自動刪除）
- [ ] 設定 Security Group（ECS 可以連 RDS，RDS 不對外開放）

### 驗收條件

- 手動執行 `docker push` 到 ECR 成功
- ECS Service 跑起來，可以打到 FastAPI `/docs`（透過 ALB 或直接 public IP）
- RDS 可以從 ECS Task 連線，不可以從外部直接連

### 對應文件

各 AWS 服務說明與指令 → `HappyMeal_AWS_Docker_CICD.md` Part 2

### 常見卡關

- IAM 權限設定錯誤是最常見的問題，ECS Task 需要兩個不同的 role（`ecsTaskExecutionRole` 和 app 專用的 task role）
- RDS 和 ECS 必須在同一個 VPC，Security Group 設定要明確允許來自 ECS 的連線
- ECR image URI 格式：`<account_id>.dkr.ecr.<region>.amazonaws.com/<repo_name>:<tag>`
- 選 `ap-northeast-1`（Tokyo）對應 HappyMeal 目標市場（台灣、香港、日本）延遲最低

---

## Step 5｜GitHub Actions CD（串接部署）

### 前置條件

- Step 3 的 CI（測試 + build）已經跑通
- Step 4 的 AWS 基礎設施已經建好

### 目標

push 到 main branch 後，自動把新的 Docker image 部署到 ECS。

### 要做的事

- [ ] 在 GitHub repo → Settings → Secrets 加入 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY`
- [ ] 在 `deploy.yml` 加入 `deploy` job（depends on `test`）
- [ ] deploy job 包含：登入 ECR → build & push image → 更新 ECS task definition → deploy service

### 驗收條件

- push 一個 commit 到 main
- GitHub Actions 的 `test` job 通過後，`deploy` job 自動接著跑
- ECS Service 更新到新版本，可以打到新 API
- `wait-for-service-stability: true` 確保 deploy 完成才結束 workflow

### 對應文件

完整 CD workflow 範例 → `HappyMeal_AWS_Docker_CICD.md` Part 3

### 常見卡關

- GitHub Secrets 的 IAM key 要用專用帳號，不要用個人帳號的 root key
- ECS task definition 更新需要先用 `describe-task-definition` 拉下現有設定，再用新 image 覆蓋，不能直接憑空產生
- deploy job 要加 `if: github.ref == 'refs/heads/main'`，避免 PR 也觸發部署

---

## 文件對照表

| 問題                         | 查這份文件                     |
| ---------------------------- | ------------------------------ |
| 要做什麼功能、驗收條件       | `PRD_v1`                       |
| 頁面結構、使用流程           | `IA_and_User_Flows_v1`         |
| 技術選型、資料模型、API 設計 | `Architecture_v1`              |
| Docker、AWS、CI/CD 實作細節  | `HappyMeal_AWS_Docker_CICD.md` |
| 從哪裡開始、順序怎麼排       | 本文件                         |

---

## 前端部署說明

前端（React + Vite）不需要 Docker 和 AWS。
直接連結 GitHub repo 到 Vercel，push 到 main 自動部署，零設定。
把心力省下來專注在後端的 Docker + AWS 流程。
