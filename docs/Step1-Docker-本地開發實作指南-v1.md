# Step 1 Docker 本地開發實作指南 v1

- 文件名稱：Step 1 Docker 本地開發實作指南
- 版本：v1
- 日期：2026-03-19
- 狀態：Draft
- 用途：定義 HappyMeal Step 1 的最小實作骨架、檔案責任、驗收流程與人機分工

---

## 1. 範圍

本文件只處理 Step 1 的本地 Docker 環境。

包含：

1. backend、frontend、db 三個服務的最小骨架
2. `docker-compose.yml` 與 `docker-compose.override.yml` 的責任切分
3. Alembic 初始化骨架
4. `.env.example`、`.gitignore` 與驗收流程

不包含：

1. LINE Login 完整串接
2. AI 食物辨識流程
3. 正式資料模型 migration
4. GitHub Actions、AWS、Zeabur 部署

---

## 2. 目前已建立的檔案

### 根目錄

- `docker-compose.yml`
- `docker-compose.override.yml`
- `.env.example`
- `.gitignore`

### backend

- `backend/Dockerfile`
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/api/routes/health.py`
- `backend/app/core/config.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`

### frontend

- `frontend/Dockerfile`
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/index.html`
- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/styles.css`

---

## 3. Compose 策略

### `docker-compose.yml`

放穩定的核心服務定義：

1. `db` 使用 PostgreSQL 16
2. `backend` 提供 FastAPI API
3. `frontend` 保留 production/build 路線的基底設定

### `docker-compose.override.yml`

只放本地開發差異：

1. `backend` 改成 `uvicorn --reload`
2. `backend` 掛載 `./backend:/app`
3. `frontend` 改成 Vite dev server
4. `frontend` 掛載 `./frontend:/app`
5. `frontend` 開放 `5173`

這樣的好處是：

1. 不需要長期維護兩個 frontend service
2. 本地開發與 production/build 可共用同一個服務名稱
3. Step 1 驗收維持 `http://localhost:5173`

---

## 4. Alembic 策略

Alembic 已納入 Step 1，但只做骨架。

目前目標：

1. 有 `alembic.ini`
2. 有 `alembic/` 目錄與 `versions/`
3. `env.py` 可讀取 `DATABASE_URL`
4. `target_metadata` 已接到 SQLAlchemy Base

目前不做：

1. 實際業務資料表 migration
2. 啟動時自動執行 migration
3. 複雜 seed data

---

## 5. 我可做的部分

1. 維護 Dockerfile、compose、override 與 `.env.example`
2. 維護 FastAPI 最小骨架與 health route
3. 維護 frontend Vite 最小骨架
4. 維護 Alembic 骨架與目錄結構
5. 補 Step 1 到 Step 2 的接續文件

---

## 6. 你需要做的部分

1. 依 `.env.example` 建立 `.env`
2. 填入本地 PostgreSQL 帳密與 `DATABASE_URL`
3. 決定第三方服務欄位是否先留空
4. 在本機安裝並啟動 Docker Desktop
5. 實際執行 `docker compose up --build`
6. 驗證 Windows 本機 port、volume 與權限是否正常

---

## 7. 最小驗收流程

1. 從 `.env.example` 複製出 `.env`
2. 補齊至少以下欄位：
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `VITE_API_BASE_URL`
3. 執行：

```bash
docker compose up --build
```

4. 確認以下結果：
   - `http://localhost:8000/docs` 可開啟
   - `http://localhost:8000/health` 回傳 `ok`
   - `http://localhost:8000/health/db` 回傳 `ok`
   - `http://localhost:5173` 可開啟

5. 進入 backend container 後，確認 Alembic 指令可用：

```bash
docker compose exec backend alembic current
```

若尚未建立 revision，沒有版本號是正常的；重點是 Alembic 可讀取設定並正常執行。

---

## 8. `.env` 最小建議值

以下是本地 Step 1 可用的最小方向：

- `APP_NAME=HappyMeal API`
- `APP_ENV=development`
- `APP_HOST=0.0.0.0`
- `APP_PORT=8000`
- `POSTGRES_DB=happymeal`
- `POSTGRES_USER=happymeal`
- `POSTGRES_PASSWORD=happymeal`
- `POSTGRES_PORT=5432`
- `DATABASE_URL=postgresql+psycopg://happymeal:happymeal@db:5432/happymeal`
- `VITE_API_BASE_URL=http://localhost:8000`

第三方欄位在 Step 1 可以先留空。

---

## 9. 常見卡關

1. `DATABASE_URL` 的主機必須是 `db`，不是 `localhost`
2. PostgreSQL ready 與 container start 不是同一件事，所以仍要看 healthcheck
3. Windows 掛 volume 時，若 Docker Desktop 沒有授權磁碟，hot reload 可能失效
4. 若 `5173` 或 `8000` 被占用，要先釋放 port 再重跑
5. `alembic current` 若失敗，先檢查 `.env` 是否真的有 `DATABASE_URL`
