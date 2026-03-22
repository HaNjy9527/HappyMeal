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
│       ├── 3. Push image → Amazon ECR
│       └── 4. Deploy → Amazon ECS (or EC2)
│
└── AWS Infrastructure
        ├── ECR          ← Docker image registry
        ├── ECS Fargate  ← 跑 backend container（FastAPI）
        ├── RDS          ← PostgreSQL
        ├── S3           ← 暫存圖片（分析完自動刪）
        └── IAM          ← 權限管理
```

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

### 2.1 ECR — Docker Image Registry

ECR 是 AWS 的 Docker Hub，用來存放你 build 好的 image。

```bash
# 建立 ECR repository
aws ecr create-repository --repository-name happymeal-backend --region ap-northeast-1

# 登入 ECR
aws ecr get-login-password --region ap-northeast-1 \
  | docker login --username AWS --password-stdin \
  <your_account_id>.dkr.ecr.ap-northeast-1.amazonaws.com

# Tag & Push
docker tag happymeal-backend:latest \
  <your_account_id>.dkr.ecr.ap-northeast-1.amazonaws.com/happymeal-backend:latest

docker push \
  <your_account_id>.dkr.ecr.ap-northeast-1.amazonaws.com/happymeal-backend:latest
```

> 選 `ap-northeast-1`（Tokyo）是因為 HappyMeal 目標市場是台灣、香港、日本，延遲最低。

### 2.2 ECS Fargate — 跑 Container 不用管伺服器

ECS Fargate 讓你只定義「要跑什麼 container、要多少資源」，不用自己開 EC2、裝 Docker。

關鍵概念：

| 概念            | 對應理解                                    |
| --------------- | ------------------------------------------- |
| Task Definition | 相當於 docker-compose 裡的一個 service 設定 |
| Service         | 確保 Task 一直在跑，掛掉會自動重啟          |
| Cluster         | 所有 Task / Service 的容器                  |
| Fargate         | Serverless 運算，不用管底層 EC2             |

**為什麼選 Fargate 而不是 EC2？**
第一版不需要管伺服器，Fargate 讓你專注在應用本身，符合 Architecture v1 降低複雜度的原則。

### 2.3 RDS — Managed PostgreSQL

```
不用自己在 EC2 裝 PostgreSQL。
RDS 幫你處理：備份、failover、版本升級。
```

設定重點：

- Engine：PostgreSQL 16
- Instance：`db.t3.micro`（Free Tier 可用）
- 放在與 ECS 同一個 VPC 的 private subnet
- Security Group 只允許來自 ECS Task 的連線，不對外開放

### 2.4 S3 — 圖片暫存與自動刪除

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

### 2.5 IAM — 權限管理

這是 AWS 最重要的基礎概念，也是最多人跳過然後踩坑的地方。

**HappyMeal 需要的角色：**

```
ecsTaskExecutionRole
├── 允許 ECS 從 ECR 拉 image
└── 允許 ECS 寫 CloudWatch logs

happymeal-backend-task-role
├── 允許讀寫 S3 happymeal-temp bucket
└── 僅此而已（最小權限原則）
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
            ├── push to ECR
            └── deploy to ECS（更新 service）
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
  ECR_REPOSITORY: happymeal-backend
  ECS_SERVICE: happymeal-backend-service
  ECS_CLUSTER: happymeal-cluster
  CONTAINER_NAME: happymeal-backend

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

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
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
        run: pytest

  deploy:
    name: Deploy to AWS
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

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }} # 用 commit hash 作為 tag
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Download ECS task definition
        run: |
          aws ecs describe-task-definition \
            --task-definition happymeal-backend \
            --query taskDefinition > task-definition.json

      - name: Update ECS task definition with new image
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: task-definition.json
          container-name: ${{ env.CONTAINER_NAME }}
          image: ${{ steps.build-image.outputs.image }}

      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true # 等 deploy 完成才結束 workflow
```

### 3.3 GitHub Secrets 設定

在 GitHub repo → Settings → Secrets and variables → Actions 加入：

| Secret 名稱             | 內容                   |
| ----------------------- | ---------------------- |
| `AWS_ACCESS_KEY_ID`     | IAM user 的 access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user 的 secret key |

> 建立一個專用的 IAM user 給 GitHub Actions 用，只給它需要的權限（ECR push + ECS deploy），不要用個人帳號的 key。

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

**Week 2 — 推上 ECR**

- [ ] 建 AWS 帳號，開 Free Tier
- [ ] 設定 IAM user（給自己用）
- [ ] 建立 ECR repository
- [ ] 手動 `docker build` + `docker push` 成功

**Week 3 — 接上 GitHub Actions**

- [ ] 寫 `.github/workflows/deploy.yml`
- [ ] 設定 GitHub Secrets
- [ ] push commit，看 Actions 跑起來
- [ ] CI（test）通過後自動 push image 到 ECR

**Week 4 — ECS 部署**

- [ ] 建 ECS Cluster + Task Definition
- [ ] 建 RDS PostgreSQL
- [ ] ECS Service 跑起來，能打到 API
- [ ] GitHub Actions deploy job 完整跑通

---

## 學到的概念清單

完成這份指南後，你會具體摸過：

**Docker**

- Dockerfile 撰寫與 multi-stage build
- docker-compose 本地多服務管理
- 環境變數注入與 secret 管理

**AWS**

- ECR：private image registry
- ECS Fargate：serverless container 運行
- RDS：managed PostgreSQL
- S3：object storage + lifecycle policy
- IAM：最小權限原則、role vs user

**GitHub Actions**

- workflow 觸發條件（push / PR）
- job 依賴關係（needs）
- AWS 官方 Actions 使用
- Secrets 管理

---

> 這份文件以 HappyMeal 的 FastAPI 後端為主要對象。
> 前端（React + Vite）部署建議維持 Vercel，那塊不需要動到 Docker 和 AWS。
