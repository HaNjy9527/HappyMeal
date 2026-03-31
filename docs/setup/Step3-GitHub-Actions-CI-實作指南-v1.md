# Step 3 GitHub Actions CI 實作指南 v1

- 文件名稱：Step 3 GitHub Actions CI 實作指南
- 版本：v1
- 日期：2026-03-23
- 狀態：Draft
- 用途：將 HappyMeal Step 3 細拆為可執行的 CI 工作包、ticket、驗收標準與範圍守門，並用新手可理解的方式說明 GitHub Actions CI 在做什麼

---

## 1. 文件定位

本文件只處理 [HappyMeal_Dev_Kickoff.md](HappyMeal_Dev_Kickoff.md) 中的 Step 3｜GitHub Actions CI。

本文件不是 Step 5｜GitHub Actions CD，也不是 AWS 正式部署操作手冊。

為避免名稱混淆，後續討論請統一使用「Step 3 CI」，不要把本文件內容混入 Step 4 或 Step 5。

---

## 2. 先理解這一步在做什麼

### 2.1 CI 是什麼

CI 是 Continuous Integration，中文常譯為持續整合。

對 HappyMeal 目前的階段來說，它不是在部署產品，而是在每次 push 或開 PR 時，自動幫你做三件事：

1. 跑 backend 自動化測試
2. 驗證 frontend 能否成功 build
3. 驗證 backend 與 frontend Docker image 能否成功 build

如果其中任何一件事失敗，代表這次變更可能會破壞主線，不能直接 merge。

### 2.2 GitHub Actions 在做什麼

GitHub Actions 是 GitHub 內建的自動化工具。

在 Step 3 裡，你只需要先掌握四個名詞：

1. workflow：整份自動化流程定義檔
2. trigger：什麼事件會啟動 workflow，例如 push 或 pull request
3. job：workflow 裡的一組工作，例如 backend-test 或 frontend-build
4. step：job 裡的一個具體步驟，例如 checkout、安裝依賴、執行 pytest

### 2.3 為什麼 Step 3 現在要做

Step 1 解決的是「本機能不能穩定跑起來」。

Step 2 解決的是「核心主流程功能有沒有做出來」。

Step 3 要解決的是「之後每次改程式時，怎麼快速知道自己有沒有把系統弄壞」。

如果沒有 CI，團隊只能靠人工記憶去跑測試與 build。這在剛開始還勉強可以，但一旦變更多，主線很容易在沒有注意到的情況下被破壞。

---

## 3. 範圍

### 3.1 納入範圍

Step 3 只聚焦在最小可行的 CI 能力，包含：

1. 建立 `.github/workflows/ci.yml`
2. backend pytest 自動化執行
3. frontend build 自動化執行
4. backend Docker build 驗證
5. frontend Docker build 驗證
6. Branch Protection Rule 設定指引
7. 失敗情境驗收

### 3.2 明確排除範圍

本文件不處理以下內容：

1. GitHub Actions CD
2. AWS credentials 設定
3. 推送 image 到 Lightsail
4. Lightsail deploy
5. RDS 建立與連線設定
6. E2E 自動化測試
7. 壓力測試與效能測試
8. 前端單元測試框架導入
9. 修改現有 backend 測試設計

### 3.3 範圍守門規則

若新需求符合以下任一條件，視為超出 Step 3：

1. 需要把 CI 延伸成 CD 或正式部署能力
2. 需要引入新的外部平台能力，例如 AWS secrets、Lightsail push、Lightsail deploy
3. 需要改造目前的 backend 測試架構，例如改成 PostgreSQL integration test 為主
4. 需要新增與目前 repo 不相符的測試框架

---

## 4. 本階段完成定義

Step 3 完成，不代表產品已可正式部署。

Step 3 的完成標準只有以下幾項：

1. GitHub Actions workflow 可被 GitHub 正常觸發
2. backend 測試在 CI 中可穩定執行
3. frontend build 在 CI 中可穩定執行
4. backend 與 frontend Docker image 在 CI 中可成功 build
5. 若 GitHub 方案支援 branch protection enforcement，PR 在 CI 失敗時會被 status check 擋住
6. 若目前 private repo 方案不支援 enforcement，需明確記錄為平台限制，並以 CI 紅燈加人工流程作為暫時替代

---

## 5. 本階段技術決策

### 5.1 為什麼 CI 先維持 SQLite

目前 backend 測試透過 [backend/tests/conftest.py](../../backend/tests/conftest.py) 使用 SQLite in-memory fixture，而不是 PostgreSQL。

Step 3 採用這個既有設計，不另外加入 PostgreSQL service container。原因如下：

1. 與現有測試一致，不需要為了 CI 重寫測試基礎設施
2. 執行速度較快
3. 設定較少，適合先把 CI 最小主鏈做穩

這不代表未來永遠不需要 PostgreSQL integration test，而是先把 Step 3 控制在目前 repo 真正需要的範圍內。

### 5.2 為什麼 frontend 先只做 build 驗證

目前 [frontend/package.json](../../frontend/package.json) 只有以下 scripts：

1. `dev`
2. `build`
3. `preview`

目前沒有前端測試指令，因此 Step 3 先把 `npm run build` 納入 CI，確認前端型別檢查與 production build 沒有壞掉。

### 5.3 為什麼要加 Docker build 驗證

HappyMeal 的部署路線是：

1. frontend 部署到 Vercel
2. backend 以 Docker image 部署到 AWS Lightsail Container Service

因此即使 Step 3 還沒進到正式部署，也應該先驗證 Docker image 能不能 build，避免到 Step 5 才發現 image 根本建不出來。

### 5.4 為什麼 branch protection 在目前 repo 不會生效

目前 HappyMeal 使用的是 private repository，而 GitHub 畫面已明確顯示 branch protection rule 為 `Not enforced`。

這代表：

1. 規則可以建立與保存
2. GitHub Actions 仍然會跑
3. 但 GitHub 不會真的用這條規則阻止 merge

因此 Step 3 在目前條件下只能驗證：

1. CI 能偵測成功與失敗
2. 失敗的 PR 會顯示紅燈
3. 團隊需要用人工流程避免合併紅燈 PR

這不是設定錯誤，而是目前 GitHub 方案對 private repo 的限制。

---

## 6. 工作包拆解

### WP-01 CI Workflow 骨架

目標：建立最小可用的 GitHub Actions workflow。

包含：

1. `.github/workflows/ci.yml`
2. push 與 pull request trigger
3. job 名稱與執行順序定義

不包含：

1. deploy job
2. AWS secrets
3. Lightsail 或 AWS 動作

完成定義：

1. workflow 檔案存在且可被 GitHub Actions 載入

### WP-02 Backend Test Job

目標：讓 backend pytest 在 GitHub Actions 自動執行。

包含：

1. Python 3.12 環境設定
2. 安裝 `backend/requirements.txt`
3. 執行 pytest

不包含：

1. PostgreSQL service container
2. migration integration test

完成定義：

1. PR 或 push 時，pytest 可在 Actions 中成功執行

### WP-03 Frontend Build Job

目標：讓 frontend production build 在 GitHub Actions 自動執行。

包含：

1. Node 22 環境設定
2. 安裝 frontend dependencies
3. 執行 `npm run build`

不包含：

1. 前端單元測試
2. 視覺回歸測試

完成定義：

1. frontend build 在 Actions 中可穩定通過

### WP-04 Docker Build Job

目標：驗證 backend 與 frontend Docker image 能夠成功建立。

包含：

1. `docker build ./backend`
2. `docker build ./frontend`

不包含：

1. push image 到 Lightsail
2. 掃描 image 安全性

完成定義：

1. backend 與 frontend image 可在 CI 中成功 build

### WP-05 Branch Protection 與失敗驗收

目標：在 GitHub 方案支援時啟用 branch protection；若不支援，則至少完成失敗情境驗收並記錄平台限制。

包含：

1. 設定 GitHub Branch Protection Rule
2. 驗證 status checks 是否會阻擋 merge
3. 若規則未 enforced，記錄平台限制與暫時替代流程

不包含：

1. CODEOWNERS
2. 強制 reviewer 數量規則

完成定義：

1. 故意製造失敗後，PR 顯示紅燈
2. 若 branch protection 已 enforced，PR 確實被擋下
3. 若 branch protection 未 enforced，文件中已明確註記限制與替代做法

---

## 7. 依賴順序

1. 先做 WP-01，沒有 workflow 骨架就無法放入任何 job
2. 再做 WP-02、WP-03、WP-04，三者是 Step 3 的核心驗證鏈
3. 最後做 WP-05，因為 Branch Protection 需要先有可用的 status checks

---

## 8. Ticket 清單

### 8.1 CI Backlog

| ID    | 任務                                 | 依賴                | 驗收條件                                                         | 明確不做                     |
| ----- | ------------------------------------ | ------------------- | ---------------------------------------------------------------- | ---------------------------- |
| CI-01 | 建立 `.github/workflows/ci.yml` 骨架 | 無                  | workflow 檔案存在且 GitHub 可辨識                                | deploy job                   |
| CI-02 | 實作 backend-test job                | CI-01               | pytest 在 Actions 中自動執行且通過                               | PostgreSQL service container |
| CI-03 | 實作 frontend-build job              | CI-01               | `npm run build` 在 Actions 中自動執行且通過                      | 前端單元測試                 |
| CI-04 | 實作 docker-build job                | CI-01               | backend 與 frontend image 可在 Actions 中 build                  | push image 到 Lightsail      |
| CI-05 | 設定 Branch Protection Rule          | CI-02, CI-03, CI-04 | 規則已建立；若平台支援則 main branch 需等待 CI 通過才能 merge    | reviewer policy              |
| CI-06 | 驗證失敗情景                         | CI-05               | 測試失敗時 PR 顯示紅燈，修正後可恢復綠燈；若平台支援則不可 merge | 壓力測試                     |

---

## 9. 驗證矩陣

本章的用途是固定 Step 3 的完成證據，以及檢查是否超出範圍。

建議每次調整 CI 時都更新一次狀態欄，狀態只使用以下三種：

1. `Not Started`
2. `In Progress`
3. `Done`

### 9.1 核心完成驗證矩陣

| 驗證面向          | 對應工作包 / Ticket | 驗證重點                                                                      | 建議證據                                      | 狀態 |
| ----------------- | ------------------- | ----------------------------------------------------------------------------- | --------------------------------------------- | ---- |
| Workflow 骨架     | WP-01, CI-01        | `.github/workflows/ci.yml` 存在且 GitHub 可載入                               | workflow 檔案、Actions 頁面截圖               | Done |
| Backend 測試      | WP-02, CI-02        | pytest 可在 Actions 中執行並通過                                              | Actions log、pytest 結果                      | Done |
| Frontend build    | WP-03, CI-03        | `npm run build` 可在 Actions 中執行並通過                                     | Actions log、build 成功輸出                   | Done |
| Docker build      | WP-04, CI-04        | backend 與 frontend Docker image 可在 CI 中成功建立                           | Actions log、docker build 成功輸出            | Done |
| Branch protection | WP-05, CI-05        | 規則已建立；目前因 private repo 方案限制為 `Not enforced`，已改以人工流程替代 | GitHub Branch Protection 設定頁、平台警告截圖 | Done |
| 失敗情境驗收      | WP-05, CI-06        | 故意讓測試失敗後，Actions 顯示紅燈；誤合併後已以 revert 撤回並恢復主線        | 失敗 run、revert commit、恢復綠燈紀錄         | Done |

### 9.2 範圍守門驗證矩陣

只要任一列出現 `Yes`，就代表超出 Step 3，不能直接算進完成定義。

| 範圍守門問題                                     | 允許答案 | 檢查方式                              | 結果 |
| ------------------------------------------------ | -------- | ------------------------------------- | ---- |
| 是否加入 GitHub Actions CD deploy job            | No       | 檢查 workflow 檔案                    | No   |
| 是否設定 AWS credentials 或 GitHub Secrets       | No       | 檢查 workflow、GitHub 設定            | No   |
| 是否 push image 到 Lightsail 或 ECR              | No       | 檢查 workflow 與 AWS 動作             | No   |
| 是否 deploy 到 Lightsail 或 ECS                  | No       | 檢查 workflow 與 AWS 動作             | No   |
| 是否導入 PostgreSQL integration test             | No       | 檢查 backend test fixture 與 workflow | No   |
| 是否引入前端新測試框架                           | No       | 檢查 `package.json` 與測試依賴        | No   |
| 是否把 Step 3 延伸成 Step 4 或 Step 5 的平台能力 | No       | 檢查文件、workflow、repo 變更         | No   |

### 9.3 平台限制註記

目前 GitHub 已顯示 branch protection rule 為 `Not enforced`，原因是 private repository 在目前方案下不支援強制執行這項保護。

因此 Step 3 需要接受以下現況：

1. 可以建立規則，但不能依賴它阻止 merge
2. 可以用故意失敗的 PR 驗證 CI 會變紅
3. 合併前仍需人工確認 PR 狀態為綠燈

在目前條件下，這項限制不視為 Step 3 失敗，而視為已確認的平台約束。

### 9.4 結案時的最終核對方式

Step 3 結案前，請依以下順序核對：

1. 先更新 9.1 的狀態欄，確認所有必要項目已達 `Done`。
2. 再更新 9.2 的結果欄，確認所有超範圍檢查仍為 `No`。
3. 若 branch protection 因平台限制未 enforced，但 9.3 已明確記錄替代流程，仍可宣告 Step 3 完成。
4. 若 9.1 有未完成項目，或 9.2 有任一列不是 `No`，不得宣告 Step 3 完成。

### 9.5 本次結案結論

以目前 HappyMeal repo 狀態，Step 3 可結案，理由如下：

1. CI workflow 已建立並成功運作
2. backend 測試、frontend build、docker build 已驗證通過
3. 故意失敗驗收已證明 CI 能正確顯示紅燈
4. branch protection 無法 enforced 已確認為 GitHub private repo 方案限制，而非設定錯誤
5. 已採用人工確認 PR 綠燈作為暫時替代流程

---

## 10. 最小驗收流程

1. 建立 `.github/workflows/ci.yml`
2. push 一個 commit 到 feature branch
3. 開 PR 到 `main`
4. 確認 GitHub Actions 自動跑出以下三個 job：
   - `backend-test`
   - `frontend-build`
   - `docker-build`
5. 確認三個 job 都為綠色
6. 故意讓一個 backend 測試失敗後再 push
7. 確認 PR 顯示紅燈；若平台支援 branch protection，則確認 PR 被 status checks 擋住
8. 修正測試並重推
9. 確認 workflow 恢復綠色

---

## 11. 常見卡關

1. `working-directory` 設錯，導致找不到 `requirements.txt` 或 `package.json`
2. Python 或 Node 版本與本機不一致，導致 CI 與本機結果不同
3. 把 Step 3 寫成 deploy workflow，直接越界進 Step 5
4. 以為一定要用 PostgreSQL service container，但現有測試其實是 SQLite fixture
5. private repo 在目前 GitHub 方案下可能出現 `Not enforced`，即使規則存在也不會真的阻止 merge

---

## 12. 你需要做的事

1. 建立 GitHub Actions workflow 檔案
2. push 一個 branch 並開 PR 驗證 CI
3. 到 GitHub repo 設定 Branch Protection Rule，並確認是否為 `Enforced` 或 `Not enforced`
4. 做一次故意失敗的驗收測試

---

## 13. 我可做的事

1. 建立 `.github/workflows/ci.yml`
2. 補齊 Step 3 文件內容
3. 根據 repo 現況調整 CI job
4. 檢查 workflow 是否越界進 CD 或 AWS deploy

---

## 14. 對應文件

1. 開發順序總覽： [HappyMeal_Dev_Kickoff.md](HappyMeal_Dev_Kickoff.md)
2. Docker 本地環境： [Step1-Docker-本地開發實作指南-v1.md](Step1-Docker-本地開發實作指南-v1.md)
3. Step 2 核心開發： [Step2-核心開發任務清單-v1.md](Step2-核心開發任務清單-v1.md)
4. Docker、AWS、Actions 背景說明： [HappyMeal_AWS_Docker_CICD.md](HappyMeal_AWS_Docker_CICD.md)
