# HappyMeal AWS Lightsail 部署指引

- 文件名稱：HappyMeal AWS Lightsail 部署指引
- 版本：v1
- 日期：2026-03-26
- 狀態：Draft
- 用途：定義 HappyMeal Step 4（AWS 設定）與 Step 5（GitHub Actions CD）的詳細操作步驟，以及 Lightsail 到 ECS 的遷移判斷標準

---

## 為什麼選 Lightsail

HappyMeal MVP 階段採用 AWS Lightsail 作為後端部署平台：
- 底層同樣是 ECS，只是 AWS 幫你包裝好
- Docker image 完全通用，日後遷移不用改程式碼
- 設定步驟減少 60% 以上，不需要自己設定 VPC / ALB / IAM Task Role
- 固定月費、內建 HTTPS，適合 MVP 階段

---

## Lightsail vs ECS Fargate 比較

| 比較項目 | Lightsail Container | ECS Fargate |
|---|---|---|
| 費用模型 | 固定月費（Nano $7 / Micro $10） | 按 vCPU + 記憶體用量計費 |
| 設定難度 | 低，Console 幾步完成 | 高，需設定 VPC / IAM / ALB |
| HTTPS | 內建，自動 TLS 憑證 | 需要 ALB + ACM，手動設定 |
| 擴展性 | 有限，手動調整，最多 20 nodes | Auto Scaling，幾乎無上限 |
| S3 整合 | 可用，需額外設定 | 原生整合 |
| RDS 連線 | 需 VPC Peering 或 Lightsail DB | 同 VPC 直接連線 |
| 監控能力 | 陽春（基本 CPU / 記憶體） | 完整 CloudWatch |
| 適合階段 | MVP、早期驗證 | 成長期、有 DevOps 人力 |

### 關鍵結論

兩個方案用的 Dockerfile 完全相同。
建議路線：**Lightsail 先上線 → 驗證產品 → 達到遷移門檻後搬到 ECS**。

---

## 什麼時候從 Lightsail 遷移到 ECS

### 流量與效能指標

- Lightsail Micro node（1 GB RAM / 0.25 vCPU）穩定支撐約 **50–200 DAU**
  - HappyMeal 的「上傳圖片 + AI 分析」是重請求，比一般 CRUD 消耗更多資源
  - 同時在線的分析請求超過 5–10 個時，Micro 會開始吃力
- CPU 持續超過 70% 且升級方案後費用已接近 ECS 成本區間（$25–50/月）
- API 平均回應時間上升，但 Lightsail 的監控看不出根本原因

### 使用者規模面

- DAU 超過 **300–500**，認真評估遷移
- 有明確尖峰時段（例如午餐時段流量是其他時段 5 倍以上），需要 Auto Scaling

### 成本交叉點

| 方案 | Lightsail 月費 | ECS Fargate 月費（估算） | 說明 |
|---|---|---|---|
| Nano / Micro | $7–10 | $12–18 | Lightsail 明顯便宜 |
| Small | $25 | $18–22（但需加 ALB $16+） | 接近持平 |
| Medium 以上 | $50+ | 視用量，可能更便宜 | ECS 開始有優勢 |

> 注意：ECS 的費用要加上 ALB（約 $16/月起）才是完整成本。

### 功能需求面（出現以下任一就值得遷移）

- 需要 AWS Secrets Manager 安全管理所有 API 金鑰
- 需要 SQS 做非同步圖片分析佇列（使用者不用等 AI 回應）
- 需要 CloudWatch Alarms 自動通知錯誤率超標
- 需要多 AZ 高可用性部署
- 需要更細緻的 IAM 權限控管

---

## Step 4 詳細操作指引（Lightsail 路線）

### 前置準備

完成 Step 1（Docker 本地跑通）和 Step 2（程式開發到可打 API）後再來這步。

### 4-A 建立 IAM User（給 GitHub Actions 用）

不論 Lightsail 或 ECS 都需要這步。

```bash
# 這些步驟在 AWS Console 操作，沒有 CLI 版本
# IAM → Users → Create user
# Username: happymeal-cicd
# Permissions: Attach policies directly
```

給予以下最小權限：

- `AmazonLightsailFullAccess`
- `AmazonS3FullAccess`（用於圖片暫存）

> 產品成長後遷移至 ECS 時，需改為 `AmazonEC2ContainerRegistryPowerUser` + `AmazonECS_FullAccess` + `AmazonS3FullAccess`。

建立 Access Key 後，將以下兩個值加入 GitHub Secrets：
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

> 永遠不要用 root 帳號或個人帳號的 key 跑 CI/CD。

---

### 4-B 建立 Lightsail Container Service

1. AWS Console → 搜尋 Lightsail → 左側 Containers
2. 點「Create container service」
3. 設定：
   - **Region**：`ap-northeast-1`（Tokyo，對台灣 / 香港 / 日本延遲最低）
   - **Power**：Micro（$10/月，新用戶前三個月免費）
   - **Scale**：1（MVP 一個 node 夠用）
   - **Service name**：`happymeal-backend`
4. Deployment 先 **Skip**（GitHub Actions 會自動部署）
5. 建立完成後取得公開 URL：

```
https://happymeal-backend.xxxxxxxx.ap-northeast-1.cs.amazonlightsail.com
```

這個 URL 即為 FastAPI 後端的 base URL，HTTPS 已自動設定。

#### 驗收條件
- Container service 狀態顯示 Ready
- 打開 URL 顯示 FastAPI 或自訂回應（尚未部署前會顯示等待頁面）

---

### 4-C 建立 Lightsail Database（PostgreSQL）

1. Lightsail 左側 → Databases → Create database
2. 設定：
   - **Database type**：PostgreSQL 16
   - **Plan**：Standard（$15/月，最小方案）
   - **Region**：`ap-northeast-1`（與 Container Service 同 Region）
   - **Master username**：自行設定（記好）
   - **Master password**：自行設定（記好）
3. 建立完成後複製 Endpoint

`DATABASE_URL` 格式：
```
postgresql://username:password@your-endpoint.ap-northeast-1.rds.amazonaws.com:5432/happymeal
```

#### 安全設定

Lightsail Database 預設對外開放，需要限制存取：
- Databases → 點進你的 DB → Networking
- 勾選「Public mode」**關閉**（或限制只允許特定 IP）
- 實際上 Lightsail Container 和 Database 在同一個 Region 可以直接連線

> 將 DATABASE_URL 加入 GitHub Secrets，名稱為 `DATABASE_URL`。

#### 驗收條件
- Database 狀態顯示 Available
- 從 container 內可以連線到 DB（Step 5 部署後驗證）

---

### 4-D 建立 S3 Bucket（圖片暫存）

這部分與原文件相同，Lightsail container 可直接呼叫 S3 API。

```bash
# 建立 bucket
aws s3api create-bucket \
  --bucket happymeal-temp \
  --region ap-northeast-1 \
  --create-bucket-configuration LocationConstraint=ap-northeast-1

# 設定 Lifecycle Policy（超過 1 小時自動刪除，雙重保險）
aws s3api put-bucket-lifecycle-configuration \
  --bucket happymeal-temp \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "DeleteTempImages",
      "Status": "Enabled",
      "Expiration": {"Days": 1},
      "Filter": {"Prefix": "temp/"}
    }]
  }'

# 確認 bucket 不對外公開
aws s3api put-public-access-block \
  --bucket happymeal-temp \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

> 對應 PRD NFR-05：原始照片僅作分析暫存，完成後刪除。

#### 後端 Python 示意（與原文件相同）

```python
import boto3

s3 = boto3.client('s3', region_name='ap-northeast-1')

# 上傳暫存
s3.upload_fileobj(image_file, 'happymeal-temp', f'temp/{analysis_id}.jpg')

# 分析完成後刪除
s3.delete_object(Bucket='happymeal-temp', Key=f'temp/{analysis_id}.jpg')
```

#### 驗收條件
- Bucket 建立成功
- 不對外公開（Public Access Block 全部 True）
- Lifecycle Policy 設定完成

---

### 4-E GitHub Secrets 完整清單

在 GitHub repo → Settings → Secrets and variables → Actions 加入：

| Secret 名稱 | 說明 |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user `happymeal-cicd` 的 Access Key |
| `AWS_SECRET_ACCESS_KEY` | IAM user 的 Secret Key |
| `DATABASE_URL` | Lightsail DB 連線字串 |
| `LINE_CHANNEL_ID` | LINE Login Channel ID |
| `LINE_CHANNEL_SECRET` | LINE Login Channel Secret |
| `AI_API_KEY` | AI 食物辨識 API 金鑰 |

> 所有敏感資訊只存在 GitHub Secrets，不出現在程式碼或 workflow yml 的明文中。
> 對應 PRD NFR-04：所有第三方 API 金鑰只能存放於後端。

---

## Step 5 GitHub Actions CD

以下是 Lightsail 版本的完整 deploy workflow：

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
          python-version: '3.12'

      - name: Install dependencies
        working-directory: ./backend
        run: pip install -r requirements.txt

      - name: Run pytest
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
        run: pytest

  deploy:
    name: Deploy to Lightsail
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

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

### Lightsail vs ECS workflow 差異對照（遷移參考）

| 步驟 | ECS 路線（遷移後） | Lightsail 路線（目前） |
|---|---|---|
| Image 存放 | Push 到 ECR | Push 到 Lightsail 內建倉庫 |
| 取得 Image URI | ECR registry URL | `get-container-images` 取最新 |
| 部署指令 | `ecs-deploy-task-definition` | `create-container-service-deployment` |
| 等待部署完成 | `wait-for-service-stability` | 無內建等待，可加 polling |
| 環境變數注入 | Task Definition | deployment `--containers` 參數 |

---

## FastAPI 需要新增的 health check endpoint

Lightsail 部署時會 health check `/health`，FastAPI 需要確保這個 route 存在：

```python
# main.py

from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

---

## 常見卡關與解法

### Lightsail 特有

| 問題 | 原因 | 解法 |
|---|---|---|
| `push-container-image` 很慢 | image 沒有 cache，每次全量上傳 | 確保 Dockerfile 善用 layer cache（先 COPY requirements.txt，再 pip install） |
| 部署後 container 一直 restart | 程式啟動失敗，health check 沒過 | 先在本地 `docker run` 測試，確認 `/health` 能回 200 |
| 連不到 Lightsail Database | public mode 關閉但 container 也連不上 | 確認 container service 和 database 在同一個 region |
| 環境變數沒生效 | deployment JSON 格式錯誤 | 用 `aws lightsail get-container-service-deployments` 查看上次部署的狀態 |

### 通用（Lightsail 和 ECS 都會遇到）

| 問題 | 原因 | 解法 |
|---|---|---|
| LINE Login callback 失敗 | callback URL 沒設定到 Lightsail 的 URL | LINE Developers Console 更新 Callback URL |
| Alembic migration 沒跑 | 部署後 DB schema 不對 | 在 container 啟動腳本中加入 `alembic upgrade head`，或另建 migration job |
| S3 權限被拒 | IAM User 沒有 S3 權限 | 確認 `happymeal-cicd` 有 `AmazonS3FullAccess` |

---

## 文件對照表（更新版）

| 問題 | 查這份文件 |
|---|---|
| 要做什麼功能、驗收條件 | `PRD_v1` |
| 頁面結構、使用流程 | `IA_and_User_Flows_v1` |
| 技術選型、資料模型、API 設計 | `Architecture_v1` |
| Docker、AWS、CI/CD 實作概念 | `HappyMeal_AWS_Docker_CICD.md` |
| 從哪裡開始、順序怎麼排 | `HappyMeal_Dev_Kickoff.md` |
| Lightsail 部署詳細步驟、遷移判斷 | **本文件** |

---

## 後續：從 Lightsail 遷移到 ECS 的路徑

當你達到遷移門檻時，步驟如下：

1. 在 ECS 建立 Cluster、Task Definition、Service
2. 將 DB 從 Lightsail Database 遷移到 AWS RDS（pg_dump / pg_restore）
3. 更新 GitHub Actions workflow，從 Lightsail 部署換成 ECS 部署
4. 更新 LINE Developers Console 的 Callback URL
5. DNS 切換

程式碼、Dockerfile 全部不需要改。
