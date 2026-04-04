# Step 5 GitHub Actions CD 實作指南 v1

- 文件名稱：Step 5 GitHub Actions CD 實作指南
- 版本：v1
- 日期：2026-03-29
- 狀態：Draft
- 用途：將 HappyMeal Step 5 細拆為可執行的 CD 工作包、ticket、驗收標準與範圍守門，並用新手可理解的方式說明 GitHub Actions CD 在做什麼

---

## 1. 文件定位

本文件只處理 [HappyMeal_Dev_Kickoff.md](HappyMeal_Dev_Kickoff.md) 中的 Step 5｜GitHub Actions CD（串接部署）。

本文件不是 Step 3｜GitHub Actions CI，也不是 Step 4｜AWS 設定。

Step 5 的前置條件：

1. Step 3 的 CI（測試 + build）已經跑通
2. Step 4 的 AWS 基礎設施已經建好

如果 Step 3 或 Step 4 任何一邊沒有完成，Step 5 不應該開始。

---

## 2. 先理解這一步在做什麼

### 2.1 CD 是什麼

CD 是 Continuous Deployment，中文常譯為持續部署。

對 HappyMeal 目前的階段來說，它的意思是：

1. 你 push 一個 commit 到 main branch
2. GitHub Actions 先自動跑測試（CI，Step 3 已經做好的事）
3. 測試通過後，GitHub Actions 自動把新版本部署到 AWS Lightsail

不需要你手動登入 AWS Console 去操作部署，也不需要你手動 build Docker image 然後 push 上去。

### 2.2 Step 5 在整個流程中的位置

```
你的程式碼 → push → GitHub Actions
                        │
                        ├── test（CI，Step 3）
                        │       │
                        │       ╰── 測試通過？
                        │             ├── 否 → 部署不會觸發，pipeline 停在這裡
                        │             ╰── 是 ↓
                        │
                        ╰── deploy（CD，Step 5）
                                │
                                ├── Build Docker image
                                ├── Push image → Lightsail 內建倉庫
                                ╰── 建立新的 Container Deployment
                                        │
                                        ╰── Lightsail 自動 health check → 服務上線
```

### 2.3 為什麼 Step 5 現在才做

Step 5 是整個開發流程的最後一哩路。它需要：

1. 有穩定的程式碼和測試（Step 2）
2. 有自動化測試把關品質（Step 3）
3. 有 AWS 基礎設施可以接收部署（Step 4）

三者都到位後，Step 5 才把它們串在一起。

### 2.4 這一步不涵蓋前端部署

前端（React + Vite）部署到 Vercel，與 GitHub Actions、AWS 無關。Vercel 直接連結 GitHub repo，push 到 main 自動部署，零設定。

本文件只處理 **後端 Docker image 部署到 AWS Lightsail** 這一條路線。

---

## 3. 範圍

### 3.1 納入範圍

Step 5 只聚焦在最小可行的 CD 能力，包含：

1. 在現有 `.github/workflows/ci.yml` 加入 `deploy` job
2. deploy job 的 AWS credentials 設定
3. Docker image build 與 push 到 Lightsail 內建倉庫
4. 建立新的 Lightsail Container Service Deployment
5. 確認 health check 通過
6. 確認 Alembic migration 在部署後可執行

### 3.2 明確排除範圍

本文件不處理以下內容：

1. 前端 Vercel 部署設定
2. 修改 AWS 基礎設施（Step 4 已完成）
3. 自動 rollback 機制
4. 多環境部署（staging / production 拆分）
5. Alembic migration 自動化執行（本階段先以手動觸發或啟動腳本為策略，不在 GitHub Actions 中直接連線 RDS 執行）
6. 壓力測試、E2E 自動化測試
7. 監控告警設定
8. Custom domain 綁定

### 3.3 範圍守門規則

若新需求符合以下任一條件，視為超出 Step 5：

1. 需要新增 staging 環境或多環境部署能力
2. 需要引入自動 rollback 或 blue-green deployment 策略
3. 需要在 GitHub Actions 中直接執行 Alembic migration（涉及 RDS 連線權限）
4. 需要新增監控、告警、日誌收集等運維能力
5. 需要修改 Step 4 已建立的 AWS 基礎設施

---

## 4. 本階段完成定義

Step 5 完成，代表後端程式碼可以從 push 到上線全程自動化。

Step 5 的完成標準只有以下幾項：

1. push 一個 commit 到 main，test job 自動執行
2. test job 通過後，deploy job 自動接著執行
3. deploy job 成功將新版 Docker image 部署到 Lightsail Container Service
4. Lightsail health check 打 `/health` 回 200，服務狀態正常
5. PR 不會觸發部署，只有 push 到 main 才會

---

## 5. 本階段技術決策

### 5.1 在 ci.yml 加入 deploy job，而不是建立獨立的 deploy.yml

有兩種做法：

1. **在現有 ci.yml 加入 deploy job**（建議）
2. 建立獨立的 deploy.yml

建議採用做法 1，原因如下：

1. ci.yml 已經有 `backend-test`、`frontend-build`、`docker-build` 三個 job，deploy job 可以直接用 `needs` 串接
2. 不需要重複定義 test job，避免浪費 GitHub Actions 分鐘數
3. 用 `if: github.ref == 'refs/heads/main'` 控制只在 push main 時觸發 deploy，PR 只跑 CI
4. MVP 階段用單一 workflow 管理整個 pipeline 比較直覺

若未來團隊規模變大、需要拆分 CI/CD 權限或引入多環境部署，再拆成獨立 workflow。

### 5.2 test job 維持 SQLite，不改成 PostgreSQL

[HappyMeal*AWS_Step4_Lightsail*部署指引-v1.md](HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md) 的 deploy workflow 範例中，test job 加入了 PostgreSQL service container。但目前 HappyMeal 的實際測試基礎設施（[backend/tests/conftest.py](../../backend/tests/conftest.py)）使用的是 SQLite in-memory fixture。

Step 5 沿用現有 SQLite 測試策略，不切換到 PostgreSQL。原因如下：

1. 與 Step 3 CI 一致，不需要為了 CD 重寫測試基礎設施
2. 測試執行速度更快，不需要等 PostgreSQL service container 啟動
3. 目前測試不涉及 PostgreSQL 特有的語法或功能
4. 測試資料庫引擎與正式環境不同的風險，在 MVP 10–100 人規模下可接受

若未來需要測試 PostgreSQL 特有行為（例如 JSON 欄位查詢、特定索引策略），再另外加入 PostgreSQL integration test，但那屬於獨立的測試升級 ticket，不屬於 Step 5。

### 5.3 /health endpoint 已存在，不需要額外新增

FastAPI 在 [backend/app/api/routes/health.py](../../backend/app/api/routes/health.py) 已經有 `/health` 路由，回傳 `{"status": "ok"}`，HTTP 200。

Lightsail Container Service 的 health check 會定期打這個路由，只要回 200 就視為健康。

另外還有 `/health/db` 路由可以檢查資料庫連線狀態，但 Lightsail health check 只需要用 `/health` 即可。

### 5.4 health check successCodes 應該用 "200" 而非 "200-499"

[HappyMeal*AWS_Step4_Lightsail*部署指引-v1.md](HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md) 的範例使用 `"successCodes": "200-499"`，範圍過寬——這意味著即使 `/health` 回 404 或 400 也會被視為健康。

建議改為 `"successCodes": "200"`，只有真正回 200 才算健康。這樣當程式啟動異常時，Lightsail 能正確偵測到問題。

### 5.5 Alembic migration 策略

部署新版程式碼後，如果資料模型有變更，資料庫 schema 必須跟著更新。目前有兩種常見做法：

1. **在 container 啟動腳本中加入 `alembic upgrade head`**：container 啟動時自動執行 migration，確保 schema 與程式碼同步
2. **手動在部署後執行 migration**：透過 `aws lightsail` CLI 或 SSH 進入 container 手動操作

MVP 階段建議採用做法 1，在 Dockerfile 的 `CMD` 改為啟動腳本：

```bash
#!/bin/sh
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

這樣每次部署都會自動確保 DB schema 是最新的。但要注意：

1. migration 應該是向前相容的（新欄位先 nullable，舊欄位不馬上刪）
2. 如果 migration 失敗，container 會無法啟動，Lightsail 會維持舊版本
3. 這不屬於 Step 5 的核心完成定義，但建議在第一次部署前確認 migration 策略

### 5.6 部署後需要更新的外部設定

第一次成功部署後，以下設定需要手動更新（不屬於 Step 5 workflow 本身，但影響功能正常運作）：

1. **CORS 設定**：把 Lightsail 的公開 URL 加入 `CORS_ALLOW_ORIGINS`，否則前端呼叫 API 會被瀏覽器擋下
2. **LINE Login Callback URL**：在 LINE Developers Console 加入 Lightsail URL 的 callback 路徑
3. **前端 API Base URL**：前端部署到 Vercel 後，API 呼叫的 base URL 需要指向 Lightsail

完整環境變數列表與各平台放置位置，請另看 [docs/setup/環境變數設定總表-v1.md](docs/setup/環境變數設定總表-v1.md)。

---

## 6. 工作包拆解

### WP-01 GitHub Secrets 確認

目標：確認 Step 4 已正確設定所有 deploy job 需要的 GitHub Secrets。

包含：

1. 確認以下 Secrets 已存在於 GitHub repo → Settings → Secrets and variables → Actions：

| Secret 名稱             | 說明                                    |
| ----------------------- | --------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | IAM user `happymeal-cicd` 的 Access Key |
| `AWS_SECRET_ACCESS_KEY` | IAM user 的 Secret Key                  |
| `CORS_ALLOW_ORIGINS`    | FastAPI CORS 白名單                     |
| `DATABASE_URL`          | Lightsail Database 連線字串             |
| `LINE_CHANNEL_ID`       | LINE Login Channel ID                   |
| `LINE_CHANNEL_SECRET`   | LINE Login Channel Secret               |
| `LINE_CALLBACK_URL`     | LINE Login callback URL                 |
| `SESSION_SECRET_KEY`    | Session 簽名密鑰                        |
| `FRONTEND_URL`          | 登入後回跳的前端網址                    |
| `AI_FOOD_API_KEY`       | AI 食物辨識 API 金鑰                    |
| `NUTRITION_DATA_SOURCE` | 營養資料來源識別字串                    |

不包含：

1. 建立 IAM User（Step 4 已完成）
2. 建立 Lightsail 資源（Step 4 已完成）

完成定義：

1. 所有 Secrets 已在 GitHub 設定頁面確認存在

### WP-02 Deploy Job 加入 ci.yml

目標：在現有 `.github/workflows/ci.yml` 加入 deploy job，串接 CI 與 CD。

包含：

1. 新增 `deploy` job
2. 設定 `needs` 依賴既有的 test / build job
3. 設定 `if: github.ref == 'refs/heads/main'` 限制只在 push main 時觸發
4. 三個核心步驟：
   - Configure AWS credentials（`aws-actions/configure-aws-credentials@v4`）
   - Build Docker image 並 push 到 Lightsail（`aws lightsail push-container-image`）
   - 建立新的 Container Service Deployment（`aws lightsail create-container-service-deployment`）

不包含：

1. 修改現有的 backend-test、frontend-build、docker-build job
2. 加入 PostgreSQL service container
3. 自動 rollback 機制

完成定義：

1. push 到 main 時，deploy job 在所有 CI job 通過後自動執行
2. PR 不會觸發 deploy job

### WP-03 Workflow 完整參考

以下是修改後的 `ci.yml` 完整結構（deploy job 部分）：

```yaml
deploy:
  name: Deploy to Lightsail
  runs-on: ubuntu-latest
  needs: [backend-test, frontend-build, docker-build]
  if: github.ref == 'refs/heads/main'

  env:
    AWS_REGION: ap-northeast-1
    LIGHTSAIL_SERVICE: happymeal-backend

  steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ap-northeast-1

    - name: Install AWS Lightsail plugin
      run: |
        curl "https://s3.us-west-2.amazonaws.com/lightsailctl/latest/linux-amd64/lightsailctl" -o "/usr/local/bin/lightsailctl"
        chmod +x /usr/local/bin/lightsailctl

    - name: Build Docker image
      run: docker build -t happymeal-backend ./backend

    - name: Push image to Lightsail
      run: |
        aws lightsail push-container-image \
          --service-name happymeal-backend \
          --label app \
          --image happymeal-backend

    - name: Deploy to Lightsail Container Service
      run: |
        IMAGE=$(aws lightsail get-container-images \
          --service-name happymeal-backend \
          --query 'containerImages[0].image' \
          --output text)

        aws lightsail create-container-service-deployment \
          --service-name happymeal-backend \
          --containers "{
            \"app\": {
              \"image\": \"$IMAGE\",
              \"environment\": {
                \"APP_ENV\": \"production\",
                \"CORS_ALLOW_ORIGINS\": \"${{ secrets.CORS_ALLOW_ORIGINS }}\",
                \"DATABASE_URL\": \"${{ secrets.DATABASE_URL }}\",
                \"LINE_CHANNEL_ID\": \"${{ secrets.LINE_CHANNEL_ID }}\",
                \"LINE_CHANNEL_SECRET\": \"${{ secrets.LINE_CHANNEL_SECRET }}\",
                \"LINE_CALLBACK_URL\": \"${{ secrets.LINE_CALLBACK_URL }}\",
                \"SESSION_SECRET_KEY\": \"${{ secrets.SESSION_SECRET_KEY }}\",
                \"FRONTEND_URL\": \"${{ secrets.FRONTEND_URL }}\",
                \"AI_FOOD_API_KEY\": \"${{ secrets.AI_FOOD_API_KEY }}\",
                \"NUTRITION_DATA_SOURCE\": \"${{ secrets.NUTRITION_DATA_SOURCE }}\"
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
              "successCodes": "200"
            }
          }'
```

> 注意：`aws lightsail push-container-image` 需要 `lightsailctl` plugin，上面已包含安裝步驟。

### WP-04 第一次部署驗證

目標：確認整個 pipeline 從 push 到服務上線可以走通。

包含：

1. push 一個 commit 到 main
2. 確認 test job 通過
3. 確認 deploy job 啟動並成功完成
4. 確認 Lightsail Container Service 更新到新版本
5. 打 Lightsail 公開 URL 的 `/health` 確認回 200

不包含：

1. 完整功能驗證
2. 壓力測試或效能測試

完成定義：

1. `https://happymeal-backend.xxxxxxxx.ap-northeast-1.cs.amazonlightsail.com/health` 回傳 `{"status": "ok"}`
2. Lightsail Console 顯示部署成功、container 狀態正常

---

## 7. 依賴順序

1. 先做 WP-01（確認 Secrets），沒有 Secrets 就不可能跑 deploy
2. 再做 WP-02（加入 deploy job），這是 Step 5 的核心工作
3. WP-03 是 WP-02 的參考範例，不需要獨立執行
4. 最後做 WP-04（第一次部署驗證），確認整條路走通

---

## 8. Ticket 清單

### 8.1 CD Backlog

| ID    | 任務                                     | 依賴        | 驗收條件                                                          | 明確不做               |
| ----- | ---------------------------------------- | ----------- | ----------------------------------------------------------------- | ---------------------- |
| CD-01 | 確認 GitHub Secrets 完整性               | Step 4 完成 | 所有必要 Secrets 已在 GitHub 設定頁面確認存在                     | 建立 IAM User          |
| CD-02 | 在 ci.yml 加入 deploy job                | CD-01       | deploy job 定義存在且語法正確；PR 不觸發 deploy；push main 才觸發 | 修改現有 CI job        |
| CD-03 | 安裝 lightsailctl plugin step            | CD-02       | deploy job 中包含 lightsailctl 安裝步驟且可正常執行               | 改用 ECR               |
| CD-04 | 實作 Docker build + push to Lightsail    | CD-03       | image 成功 push 到 Lightsail 內建倉庫                             | 多架構 build           |
| CD-05 | 實作 create-container-service-deployment | CD-04       | Lightsail 收到部署指令並開始 rolling update                       | 自動 rollback          |
| CD-06 | 第一次完整 pipeline 驗證                 | CD-05       | push → test → deploy → health check 200                           | 效能測試、完整功能驗證 |

---

## 9. 驗證矩陣

### 9.1 核心完成驗證矩陣

| 驗證面向             | 對應工作包 / Ticket | 驗證重點                                     | 建議證據                                  | 狀態        |
| -------------------- | ------------------- | -------------------------------------------- | ----------------------------------------- | ----------- |
| GitHub Secrets       | WP-01, CD-01        | 所有必要 Secrets 已正確設定                  | GitHub Secrets 設定頁截圖（不含值）       | Done        |
| Deploy job 定義      | WP-02, CD-02        | deploy job 存在，`needs` 與 `if` 設定正確    | ci.yml 檔案內容、workflow graph 截圖      | Done        |
| lightsailctl 安裝    | WP-02, CD-03        | deploy job 中 lightsailctl 可正常安裝與使用  | Actions log                               | Done        |
| Image push           | WP-02, CD-04        | Docker image 成功 push 到 Lightsail 內建倉庫 | Actions log、Lightsail Console image 清單 | Done        |
| Container deployment | WP-02, CD-05        | Lightsail 成功建立新部署，container 狀態正常 | Lightsail Console deployment 紀錄         | Done        |
| Health check         | WP-04, CD-06        | `/health` 回 200                             | `curl` 回應截圖                           | Done        |
| PR 不觸發 deploy     | WP-02, CD-02        | 開 PR 時只跑 CI job，deploy job 顯示 skipped | PR 的 Actions 頁面截圖                    | Not Started |

### 9.2 範圍守門驗證矩陣

只要任一列出現 `Yes`，就代表超出 Step 5，不能直接算進完成定義。

| 範圍守門問題                                      | 允許答案 | 檢查方式                         | 結果 |
| ------------------------------------------------- | -------- | -------------------------------- | ---- |
| 是否修改了現有 CI job 的行為                      | No       | 檢查 ci.yml 的 diff              |      |
| 是否切換 test job 到 PostgreSQL service container | No       | 檢查 ci.yml 是否有 services 區塊 |      |
| 是否加入自動 rollback 機制                        | No       | 檢查 workflow 邏輯               |      |
| 是否加入 staging / production 多環境部署          | No       | 檢查 workflow 與 branch 策略     |      |
| 是否修改 AWS 基礎設施設定                         | No       | 檢查 Lightsail Console           |      |
| 是否加入監控告警或日誌收集                        | No       | 檢查 workflow 與 AWS 設定        |      |
| 是否在 GitHub Actions 中直接連 RDS 跑 migration   | No       | 檢查 workflow steps              |      |

### 9.3 結案時的最終核對方式

Step 5 結案前，請依以下順序核對：

1. 先更新 9.1 的狀態欄，確認所有必要項目已達 `Done`。
2. 再更新 9.2 的結果欄，確認所有超範圍檢查仍為 `No`。
3. 若 9.1 有未完成項目，或 9.2 有任一列不是 `No`，不得宣告 Step 5 完成。

---

## 10. 常見卡關

| 問題                                             | 原因                                            | 解法                                                                        |
| ------------------------------------------------ | ----------------------------------------------- | --------------------------------------------------------------------------- |
| `push-container-image` 失敗，找不到 lightsailctl | 未安裝 lightsailctl plugin                      | 在 deploy job 中加入安裝 lightsailctl 的步驟                                |
| `push-container-image` 非常慢                    | image 沒有 layer cache，每次全量上傳            | 確保 Dockerfile 中先 COPY requirements.txt 再 pip install，善用 layer cache |
| deploy 成功但 container 一直 restart             | 程式啟動失敗或 health check 沒過                | 先在本地 `docker run` 測試，確認 `/health` 能回 200                         |
| deploy job 在 PR 時也跑了                        | 缺少 `if` 條件判斷                              | 加上 `if: github.ref == 'refs/heads/main'`                                  |
| 環境變數沒生效                                   | deployment JSON 格式錯誤（引號跳脫等）          | 用 `aws lightsail get-container-service-deployments` 查看部署詳情           |
| Lightsail 連不到 Database                        | Container Service 和 Database 不在同一個 Region | 確認兩者都在 `ap-northeast-1`                                               |
| API 回應被瀏覽器 CORS 擋下                       | Lightsail URL 未加入 `CORS_ALLOW_ORIGINS`       | 部署成功後，把 Lightsail 公開 URL 加入 FastAPI CORS 設定                    |
| LINE Login callback 失敗                         | callback URL 還指向 localhost                   | 在 LINE Developers Console 加入 Lightsail URL 的 callback 路徑              |
| Migration 未執行導致 500 錯誤                    | 程式碼引用了新欄位但資料庫 schema 還是舊的      | 確認 migration 策略（啟動腳本或手動執行），詳見 5.5 節                      |

---

## 11. 對應文件

| 問題                                    | 查這份文件                                                                                   |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| CD workflow 範例與 Lightsail 操作步驟   | [HappyMeal*AWS_Step4_Lightsail*部署指引-v1.md](HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md) |
| Docker、AWS、CI/CD 全局概念             | [HappyMeal_AWS_Docker_CICD.md](HappyMeal_AWS_Docker_CICD.md)                                 |
| 現有 CI workflow 骨架與 Step 3 決策紀錄 | [Step3-GitHub-Actions-CI-實作指南-v1.md](Step3-GitHub-Actions-CI-實作指南-v1.md)             |
| 部署平台選型與成本預估                  | [部署與用量預估-v1.md](../部署與用量預估-v1.md)                                              |
| Lightsail 到 ECS 遷移門檻               | [HappyMeal*AWS_Step4_Lightsail*部署指引-v1.md](HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md) |
| 從哪裡開始、順序怎麼排                  | [HappyMeal_Dev_Kickoff.md](HappyMeal_Dev_Kickoff.md)                                         |
