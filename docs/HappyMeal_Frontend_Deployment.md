# HappyMeal 前端部署策略

- 文件名稱：HappyMeal 前端部署策略
- 版本：v1
- 日期：2026-03-22
- 狀態：Draft
- 用途：釐清前端 Dockerfile 的用途、Vercel 部署方式、以及與後端部署的分工邊界

---

## 核心觀念：前端不需要 Docker 部署

前端 build 出來的東西沒有 runtime，它不是一個持續跑著的 process，只是一堆靜態檔案等著被瀏覽器下載。

```
後端（FastAPI）    = 持續跑著的 Python process  → 需要 container
資料庫（PostgreSQL）= 持續跑著的 DB process     → 需要 container
前端（React build） = 靜態檔案                  → 不需要 container
```

Docker 的核心價值是打包一個執行環境，但靜態檔案不需要執行環境，任何 CDN 都可以服務它。

---

## 本地 frontend Dockerfile 的用途

文件裡雖然有 frontend Dockerfile，但它的目的是**本地開發用的 Vite dev server**，不是為了部署。

```
本地開發    → frontend container 跑 Vite dev server（hot reload）
部署到生產  → npm run build → 靜態檔 → Vercel 服務
```

**本地 frontend Dockerfile 只活在 docker-compose 裡，不會被推到 ECR，也不會跑在 ECS 上。**

### 本地兩種模式對照

專案採用 `docker-compose.yml` + `docker-compose.override.yml` 分層策略：

- `docker-compose.yml` 定義基底設定，frontend 的 build target 為 `production`（nginx 靜態檔）
- `docker-compose.override.yml` 覆寫為 `dev` target（Vite dev server + hot reload）
- Docker Compose 預設自動合併 override，所以日常開發只需 `docker compose up`

| 模式            | 用途                           | 指令                                      |
| --------------- | ------------------------------ | ----------------------------------------- |
| Vite dev server | 日常開發，hot reload           | `docker compose up`                       |
| nginx 靜態檔    | 驗證 production build 是否正常 | `docker compose -f docker-compose.yml up` |

> 第二種指令只指定 base compose 檔，跳過 override，frontend 就會走 production target。

詳細 Dockerfile 策略 → `HappyMeal_AWS_Docker_CICD.md` Part 1

---

## Vercel 能做什麼

Vercel 不只是靜態網站托管，對 HappyMeal 來說最關鍵的功能是：

- React + Vite build 後的靜態檔 CDN 托管
- 全球 CDN 加速
- 自動 HTTPS
- 連結 GitHub repo 後，push to main 自動重新 build 和部署
- 零設定，不需要寫任何 CI/CD

---

## Monorepo 結構下的 Vercel 設定

HappyMeal 前後端放在同一個 repo，Vercel 完全支援這種結構，透過 **Root Directory** 指定前端位置即可。

### 專案結構

```
HappyMeal/
├── backend/          ← FastAPI，Vercel 不管這裡
├── frontend/         ← 指定這個給 Vercel
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docs/
└── docker-compose.yml
```

### Vercel 設定

在 Vercel dashboard 連結 GitHub repo 後，設定以下三個欄位：

| 欄位             | 值              |
| ---------------- | --------------- |
| Root Directory   | `frontend`      |
| Build Command    | `npm run build` |
| Output Directory | `dist`          |

Vercel 只會進到 `frontend/` 資料夾，執行 build，把 `dist/` 裡的東西部署出去，完全不會理會旁邊的 `backend/`。

---

## API Base URL 環境變數處理

前端的 API base URL 需要在 build 時指向正確的後端位置，本地和生產環境不同，透過環境變數處理。

```bash
# 本地 .env（不 commit）
VITE_API_BASE_URL=http://localhost:8000

# Vercel 環境變數（在 Vercel dashboard 設定，不需要推上 repo）
VITE_API_BASE_URL=https://api.happymeal.com
```

Vercel 有自己的環境變數設定介面，在 dashboard → Settings → Environment Variables 填入即可。

---

## 整體部署架構

```
使用者瀏覽器
      │
      ├── 靜態資源請求 → Vercel CDN（React build）
      │
      └── API 請求 → AWS ECS（FastAPI）→ AWS RDS（PostgreSQL）
```

### 兩條部署流水線

```
同一個 GitHub repo
        │
        ├── frontend/ 有變動
        │       └── Vercel 自動偵測 → npm run build → 部署 CDN
        │
        └── backend/ 有變動
                └── GitHub Actions → Docker build
                      → push ECR → deploy ECS
```

兩條流水線共用同一個 repo，互不干擾。

---

## 各服務分工總結

| 服務    | 負責什麼              | 在哪裡跑           |
| ------- | --------------------- | ------------------ |
| Vercel  | 前端靜態檔 CDN        | Vercel 平台        |
| AWS ECS | FastAPI 後端          | AWS ap-northeast-1 |
| AWS RDS | PostgreSQL            | AWS ap-northeast-1 |
| AWS S3  | 圖片暫存              | AWS ap-northeast-1 |
| AWS ECR | Docker image registry | AWS ap-northeast-1 |

---

## 相關文件

| 文件                           | 內容                                             |
| ------------------------------ | ------------------------------------------------ |
| `HappyMeal_AWS_Docker_CICD.md` | Docker 容器化、AWS 服務、GitHub Actions 完整指南 |
| `HappyMeal_Dev_Kickoff.md`     | 實作起點順序與驗收條件                           |
| `Architecture_v1`              | 技術選型與系統架構                               |
