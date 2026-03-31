# HappyMeal × AWS × Docker — CI/CD 實戰指南

> 目的：以 HappyMeal 專案為載體，實際摸過 Docker 容器化、GitHub Actions 自動化部署、以及基本 AWS 服務操作。
> 學習策略：Docker 為主軸，AWS 為部署目標，GitHub Actions 串接全流程。
> **注意：本文件的程式片段為學習用簡化範例，實際檔案以 repo 內的 `backend/Dockerfile`、`frontend/Dockerfile`、`docker-compose.yml`、`docker-compose.override.yml` 為準。**

---

## 全局架構圖

```
GitHub Repo
│
├── push to main
│       │
│       ▼
│   GitHub Actions (CI/CD)
│       │
│       ├── 1. Run tests
│       ├── 2. Docker build
│       ├── 3. Push image → Lightsail 內建倉庫
│       └── 4. Deploy → Lightsail Container Service
│
└── AWS Infrastructure
        ├── Lightsail Container Service ← 跑 backend container（FastAPI）
        ├── Lightsail Database          ← PostgreSQL
        ├── S3                          ← 暫存圖片（分析完自動刪）
        └── IAM                         ← 權限管理
```

> MVP 階段使用 Lightsail，降低設定門檻與固定月費。Dockerfile 與 ECS Fargate 完全通用，產品成長後可無痛遷移。

---

## Part 1｜Docker 容器化（主軸）

### 1.1 後端 Dockerfile（FastAPI）

```dockerfile
# backend/Dockerfile

FROM python:3.12-slim

WORKDIR /app

# 先複製 requirements 利用 cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 前端 Dockerfile（React + Vite）

```dockerfile
# frontend/Dockerfile

# Stage 1: build
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve（用 nginx 提供靜態檔）
FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

> **Multi-stage build** 是關鍵概念：build 環境和執行環境分離，image 更小、更安全。

### 1.3 本地開發用 docker-compose

> 實際專案採用 `docker-compose.yml` + `docker-compose.override.yml` 分層策略，以下為簡化範例。

```yaml
# docker-compose.yml

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://happymeal:happymeal@db:5432/happymeal
      - LINE_CHANNEL_ID=${LINE_CHANNEL_ID}
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - AI_API_KEY=${AI_API_KEY}
    depends_on:
      - db
    volumes:
      - ./backend:/app # hot reload in dev

  frontend:
    build: ./frontend
    ports:
      - "5173:80"
    depends_on:
      - backend

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: happymeal
      POSTGRES_PASSWORD: happymeal
      POSTGRES_DB: happymeal
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 1.4 .env 管理原則

```bash
# .env.example（commit 這個）
LINE_CHANNEL_ID=
LINE_CHANNEL_SECRET=
AI_API_KEY=
DATABASE_URL=

# .env（加入 .gitignore，不 commit）
LINE_CHANNEL_ID=your_real_value
```

> 對應 PRD NFR-04：所有第三方 API 金鑰只能存放於後端。Docker 的環境變數注入是實現這件事的標準方式。

---

## Part 2｜AWS 服務（部署目標）

### 2.1 Lightsail Container Service — 跑 Container 最簡單的方式

Lightsail Container Service 是 AWS 對 ECS Fargate 的簡化包裝。不需要自己設定 VPC、ALB、IAM Task Role，Console 幾步就能完成。

關鍵特性：

| 特性            | 說明                                               |
| --------------- | -------------------------------------------------- |
| 固定月費        | Nano $7 / Micro $10（新用戶前三個月免費）          |
| 內建 HTTPS      | 自動 TLS 憑證，不需要另外設定 ALB + ACM            |
| 內建 Image 倉庫 | 不需要另外建 ECR，直接 `push-container-image` 即可 |
| 與 ECS 通用     | Dockerfile 完全相同，日後遷移不需改程式碼          |

**為什麼 MVP 選 Lightsail 而不是 ECS Fargate？**
第一版不需要複雜的 VPC / ALB / IAM Role 設定，Lightsail 讓你專注在應用本身，符合 Architecture v1 降低複雜度的原則。產品成長後可無痛遷移至 ECS Fargate，詳見 `HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md`。

### 2.2 Lightsail Database — Managed PostgreSQL

不用自己在 EC2 裝 PostgreSQL。Lightsail Database 幫你處理備份與基本維運。

設定重點：

- Engine：PostgreSQL 16
- Plan：Standard（$15/月，最小方案）
- Region：`ap-northeast-1`（與 Container Service 同 Region）
- 關閉 Public mode，僅允許同 Region 的 Lightsail Container 連線

### 2.3 S3 — 圖片暫存與自動刪除

對應 PRD FR-03 + NFR-05：圖片只暫存分析，完成後刪除。

```python
# 後端處理邏輯示意
import boto3

s3 = boto3.client('s3')

# 上傳暫存
s3.upload_fileobj(image_file, 'happymeal-temp', f'temp/{analysis_id}.jpg')

# 分析完成後刪除
s3.delete_object(Bucket='happymeal-temp', Key=f'temp/{analysis_id}.jpg')
```

S3 也可以設定 Lifecycle Policy，超過 1 小時的物件自動刪除，作為雙重保險。

### 2.4 IAM — 權限管理

這是 AWS 最重要的基礎概念，也是最多人跳過然後踩坑的地方。

**HappyMeal Lightsail 路線需要的權限：**

```
happymeal-cicd (IAM User)
├── AmazonLightsailFullAccess
└── AmazonS3FullAccess
```

> 永遠不要用 root account 或 AdministratorAccess 跑應用程式。

---

## Part 3｜GitHub Actions CI/CD（串接全流程）

### 3.1 整體流程設計

```
push to main
    │
    ├── [CI] run-tests job
    │       ├── pytest（後端）
    │       └── 通過才繼續
    │
    └── [CD] deploy job（depends on CI）
            ├── docker build
            ├── push to Lightsail 內建倉庫
            └── deploy to Lightsail Container Service
```

### 3.2 完整 workflow 檔案

```yaml
# .github/workflows/deploy.yml

name: HappyMeal CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: ap-northeast-1
  LIGHTSAIL_SERVICE: happymeal-backend

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        working-directory: ./backend
        run: pip install -r requirements.txt

      - name: Run pytest
        working-directory: ./backend
        run: pytest

  deploy:
    name: Deploy to Lightsail
    runs-on: ubuntu-latest
    needs: test # 測試通過才部署
    if: github.ref == 'refs/heads/main' # 只有 main branch 才部署

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Build Docker image
        run: docker build -t happymeal-backend ./backend

      - name: Push image to Lightsail
        run: |
          aws lightsail push-container-image \
            --service-name ${{ env.LIGHTSAIL_SERVICE }} \
            --label app \
            --image happymeal-backend

      - name: Deploy to Lightsail Container Service
        run: |
          IMAGE=$(aws lightsail get-container-images \
            --service-name ${{ env.LIGHTSAIL_SERVICE }} \
            --query 'containerImages[0].image' \
            --output text)

          aws lightsail create-container-service-deployment \
            --service-name ${{ env.LIGHTSAIL_SERVICE }} \
            --containers "{
              \"app\": {
                \"image\": \"$IMAGE\",
                \"environment\": {
                  \"DATABASE_URL\": \"${{ secrets.DATABASE_URL }}\",
                  \"LINE_CHANNEL_ID\": \"${{ secrets.LINE_CHANNEL_ID }}\",
                  \"LINE_CHANNEL_SECRET\": \"${{ secrets.LINE_CHANNEL_SECRET }}\",
                  \"AI_API_KEY\": \"${{ secrets.AI_API_KEY }}\"
                },
                \"ports\": { \"8000\": \"HTTP\" }
              }
            }" \
            --public-endpoint '{
              "containerName": "app",
              "containerPort": 8000,
              "healthCheck": {
                "path": "/health",
                "intervalSeconds": 10,
                "timeoutSeconds": 5,
                "successCodes": "200-499"
              }
            }'
```

### 3.3 GitHub Secrets 設定

在 GitHub repo → Settings → Secrets and variables → Actions 加入：

| Secret 名稱             | 內容                                    |
| ----------------------- | --------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | IAM user `happymeal-cicd` 的 Access Key |
| `AWS_SECRET_ACCESS_KEY` | IAM user 的 Secret Key                  |
| `DATABASE_URL`          | Lightsail DB 連線字串                   |
| `LINE_CHANNEL_ID`       | LINE Login Channel ID                   |
| `LINE_CHANNEL_SECRET`   | LINE Login Channel Secret               |
| `AI_API_KEY`            | AI 食物辨識 API 金鑰                    |

> 建立一個專用的 IAM user 給 GitHub Actions 用，只給它需要的權限（Lightsail + S3），不要用個人帳號的 key。
> 所有敏感資訊只存在 GitHub Secrets，不出現在程式碼或 workflow yml 的明文中。

### 3.4 PR 與 main branch 策略

```
feature/xxx  →  PR  →  main
                 │
                 ├── CI 跑 test（PR 開啟時觸發）
                 └── merge 後觸發 deploy
```

好習慣：設定 Branch Protection Rule，要求 CI 通過才能 merge。

---

## Part 4｜順序建議

從零開始的實作順序，每個階段都有可驗證的結果：

**Week 1 — Docker 本地跑起來**

- [ ] 寫 backend Dockerfile
- [ ] 寫 docker-compose（backend + db）
- [ ] `docker compose up` 後 FastAPI `/docs` 能開
- [ ] 確認環境變數注入正確

**Week 2 — 建立 AWS Lightsail 基礎設施**

- [ ] 建 AWS 帳號，開 Free Tier
- [ ] 設定 IAM user（`happymeal-cicd`）
- [ ] 建立 Lightsail Container Service
- [ ] 建立 Lightsail Database

**Week 3 — 接上 GitHub Actions**

- [ ] 寫 `.github/workflows/deploy.yml`
- [ ] 設定 GitHub Secrets
- [ ] push commit，看 Actions 跑起來
- [ ] CI（test）通過後自動 push image 到 Lightsail

**Week 4 — Lightsail 部署完整跑通**

- [ ] 部署後可以打到 FastAPI `/docs`
- [ ] Health check 通過
- [ ] GitHub Actions deploy job 完整跑通

---

## 學到的概念清單

完成這份指南後，你會具體摸過：

**Docker**

- Dockerfile 撰寫與 multi-stage build
- docker-compose 本地多服務管理
- 環境變數注入與 secret 管理

**AWS**

- Lightsail Container Service：簡化的 container 運行環境
- Lightsail Database：managed PostgreSQL
- S3：object storage + lifecycle policy
- IAM：最小權限原則、role vs user
- （後續遷移）ECR + ECS Fargate：產品成長期的容器部署方案

**GitHub Actions**

- workflow 觸發條件（push / PR）
- job 依賴關係（needs）
- AWS 官方 Actions 使用
- Secrets 管理

---

> 這份文件以 HappyMeal 的 FastAPI 後端為主要對象。
> 前端（React + Vite）部署建議維持 Vercel，那塊不需要動到 Docker 和 AWS。
