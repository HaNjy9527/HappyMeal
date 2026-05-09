# HappyMeal PRD 實作進度與下一步 v1

- 文件名稱：HappyMeal PRD 實作進度與下一步
- 版本：v1
- 日期：2026-04-20
- 最後更新：2026-05-09（Priority 4、Priority 5 完成）
- 狀態：Draft
- 用途：對照 `PRD-v1.md` 與目前 repo 實作狀態，整理已完成、部分完成、未完成項目，並提出下一個開發優先順序。

---

## 1. 文件定位

本文件不是新的產品需求文件，不取代 [PRD-v1.md](./PRD-v1.md)。

本文件的用途只有兩件事：

1. 盤點目前程式碼相對於 PRD v1 的落地進度
2. 為下一輪開發提供優先順序建議

若要修改產品範圍、成功指標、角色、MVP 邊界，應回到 [PRD-v1.md](./PRD-v1.md) 更新。

若要追蹤 Step 2 工作包、Ticket 與驗收矩陣，仍以 [setup/Step2-核心開發任務清單-v1.md](./setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md) 為準。

補充說明：

1. 本文件處理的是「PRD v1 尚未補齊的產品缺口」，不是重新定義 Step 1 到 Step 5 的開發順序
2. 截至 2026-04，專案的 CI/CD 與 AWS 部署鏈路已經建立，因此目前討論的 Priority 1 到 Priority 5，應視為「產品補完優先順序」，不是「開發起點步驟」
3. 若要避免混淆，閱讀上建議把 `Step 1-5` 視為歷史開發路徑，把 `Priority 1-5` 視為目前活躍中的補齊主題

---

## 2. 判讀範圍與依據

本次判讀依據以下來源：

1. 產品需求： [PRD-v1.md](./PRD-v1.md)
2. 頁面與流程： [IA-User-Flows-v1.md](./IA-User-Flows-v1.md)
3. 系統模組與資料模型： [System-Architecture-v1.md](./System-Architecture-v1.md)
4. Step 2 工作包與完成矩陣： [setup/Step2-核心開發任務清單-v1.md](./setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md)
5. 目前前後端程式碼與測試

本文件的狀態分級只使用以下三種：

1. 已完成：已有可用的前後端能力，且與 PRD 要求大致一致
2. 部分完成：主鏈已打通，但仍有 mock、缺頁面、缺正式資料來源，或驗收條件尚未完全達標
3. 尚未完成：目前 repo 尚未看見足夠實作

---

## 3. 目前總結

以目前 repo 狀態來看：

1. 若以 Step 2 核心開發為標準，主要工作已大致完成
2. 若以 PRD v1 完整 MVP 體驗為標準，整體約落在「主鏈已通，但仍需補齊正式能力與使用者可見流程」的階段
3. 目前最明確已完成的項目是 LINE Login、Profile、Theme、Consent API、最小版 Consent Intro、Analysis 主鏈、History 主鏈、GPT / OpenAI 食物辨識最小路徑與後端測試骨架
4. 目前最明確未做滿的項目是 AI 辨識穩定性與分流驗收、正式營養資料來源的完整 coverage，以及 IA 中較完整的頁面體驗

版本判讀上，建議把目前狀態視為 `V1 MVP / Beta`：核心單次餐點分析主鏈已可驗證。接下來的 `V1.X` 是把 PRD v1 尚未補齊的缺口收斂到 `V1.0 Release`，不是 PRD v2。

另外，文件閱讀上需要先分清楚兩件事：

1. `Step 1-5` 是當初的開發順序文件，用來說明先本地、再 CI、再 AWS、再 CD 的路徑
2. `Priority 1-5` 是目前產品補齊順序，用來說明接下來該優先補哪條功能主鏈

因此，現在若要跟進開發進度，應優先看本文件第 7 節與對應的 Priority 細文件，而不是再把 Step 4 或 Step 5 當作待做事項。

---

## 3.1 目前開發步驟狀態

為避免文件中的 `Step` 與 `Priority` 混在一起，先單獨列出目前專案所處位置：

| 路徑   | 原始用途                 | 目前狀態       | 現在應如何使用                             |
| ------ | ------------------------ | -------------- | ------------------------------------------ |
| Step 1 | Docker 本地開發基線      | 已完成         | 當環境壞掉或新同伴加入時，作為本地環境參考 |
| Step 2 | 核心主流程開發與驗收     | 主鏈已大致完成 | 作為 scope baseline 與驗收矩陣參考         |
| Step 3 | GitHub Actions CI        | 已完成         | 作為 CI 設定與維護參考                     |
| Step 4 | AWS / Lightsail 基礎設施 | 已完成         | 作為部署環境維護參考                       |
| Step 5 | GitHub Actions CD        | 已完成         | 作為部署流程維護參考                       |

結論：

1. 目前不應再把 Step 4 或 Step 5 寫成「下一步開發優先順序」
2. 目前真正的下一步，應聚焦在 PRD v1 尚未補齊的產品缺口
3. 這些缺口已改由本文件第 7 節與其拆分文件來承接

---

## 4. PRD 功能對照表

| PRD 項目 | 功能名稱              | 目前狀態 | 目前判讀                                                                                                            | 備註                                                             |
| -------- | --------------------- | -------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| FR-01    | LINE Login 註冊與登入 | 已完成   | 後端已具備 LINE OAuth、callback、signed token exchange、session、`/auth/me`、logout；前端也已串登入頁與受保護頁流程 | 目前可視為已完成                                                 |
| FR-02    | 個人資料管理          | 已完成   | 已支援 profile 讀取與更新，包含 age、height、weight、activity、goal、goal weight                                    | 已能支撐 recommendation                                          |
| FR-03    | 拍照與圖片上傳        | 部分完成 | 已支援 JPG、PNG 上傳與大小限制，並在完成後刪除暫存圖片                                                              | 手機相機體驗與前端流程仍屬最小版                                 |
| FR-04    | 食物辨識              | 部分完成 | GPT / OpenAI provider 已接上；`success`、`partial`（`confidence_score < 0.6`）、`complete_failure` 三種狀態均已落地並可由前端分流；仍需補最小觀測性與手機驗測 | 辨識分流已完成；正式完成前仍需觀測性與實機驗收 |
| FR-05    | 手動修正與份量確認    | 已完成   | 前端可修改 food name 與 portion，後端可接收 confirm 結果並寫入 item                                                 | 已可完成候選確認                                                 |
| FR-06    | 營養估算              | 部分完成 | 已具備 canonical mapping、official source catalog、unit normalization 與 fallback 策略；metadata 可追溯，`is_anomalous` 提供粗估警示；official catalog coverage 仍屬 MVP 範圍，後續可依真實樣本擴充 | Priority 3 已完成；完整 nutrition source coverage 仍需長期累積 |
| FR-07    | 增肌／減脂建議        | 已完成   | 已依 profile 與 goal 產生 target calories、macro 與推薦運動，語氣仍維持 wellness guidance                           | 已能形成 MVP 第一層建議                                          |
| FR-08    | 熱門運動熱量消耗      | 部分完成 | 已有 20 筆 ExerciseCatalog seed，confirm 後可推薦 3 個運動並估算消耗                                                | 尚未形成獨立查詢頁或完整查詢體驗                                 |
| FR-09    | 分析歷史              | 已完成   | 已有 history list 與 detail，且回傳建議快照，不保存原始圖片                                                         | 符合主鏈需求                                                     |
| FR-10    | 主題切換              | 已完成   | theme_preference 已可跨裝置保存，前端可切換兩種主題；Theme Preference UI 已整合進 Profile 側欄並完成中文化          | Priority 4 已補齊頁面結構                                        |
| FR-11    | 同意與聲明            | 已完成   | Consent 與非醫療提醒主鏈已完成，包含必要同意、guidance guard、日常回看入口、短版提醒、手機實機驗收與整體 IA 整合    | Priority 1 + Priority 4 合計完成                                  |

---

## 5. 驗收條件對照表

| 驗收條件                                         | 目前狀態 | 判讀                                                                                                 |
| ------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------------------- |
| 使用者可在手機完成登入、建檔、拍照分析與查看建議 | 部分完成 | 主鏈與 Priority 1 手機實機驗收已完成最小版，但完整 Home / IA 體驗仍需精修                            |
| AI 辨識失準時，使用者可手動修正後完成流程        | 已完成   | GPT / OpenAI 候選可進入 candidate review，手動修正與 confirm 主鏈已可操作                            |
| 歷史紀錄可查看過去分析摘要與建議快照             | 已完成   | history list 與 detail 已具備                                                                        |
| 系統不長期保存原始圖片                           | 已完成   | analysis 完成後會刪除暫存圖片                                                                        |
| 主題切換後重新登入仍保留偏好                     | 部分完成 | 偏好保存已完成，但仍建議補實際跨裝置手動驗收紀錄                                                     |
| 所有建議相關頁面皆顯示非醫療用途提醒             | 已完成   | Analysis Result 與 History Detail 已改在 recommendation 區塊附近顯示短版提醒；全站頁尾回看入口已補齊 |

---

## 6. 與 Step 2 的關係

目前狀態可以概括為：

1. Step 2 的最小主流程驗證已大致達標
2. 但 Step 2 的完成，不等於 PRD v1 的完整 MVP 體驗完成
3. 目前差距主要集中在「正式能力」與「使用者可見流程補齊」，而不是基礎 CRUD 或資料模型

最重要的落差如下：

1. GPT / OpenAI 食物辨識已接上，`partial` 判定已落地，但最小觀測性與手機實機驗測仍需補齊
2. Priority 3 已全數完成（canonical mapping、unit normalization、nutrition source 層級、metadata 可追溯性、history 結果重用），official catalog coverage 仍屬 MVP 範圍，後續可依真實樣本擴充
3. Consent Intro 已完成最小版；Landing / Home / Theme 等 IA 頁面已於 Priority 4 完成產品化
4. 手機優先體驗已於 Priority 4 收斂，主頁面不再有測試頁感受

---

## 7. 下一個開發優先順序

本節的目的不是擴張新需求，而是先補齊 PRD v1 尚未完成的缺口。

為了避免本文件一次涵蓋太多內容，以下只保留 Priority 總覽；各 Priority 的詳細拆解、範圍、驗收條件與目前狀態，已拆到獨立文件。

### 7.1 Priority 總覽表

| Priority   | 主題                       | 目標                                                      | 詳細文件                                                                                                                                                                                                |
| ---------- | -------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Priority 1 | Consent 與非醫療提醒主鏈   | 已完成 V1 最小版，後續精修移交 Priority 4                 | [功能開發/Priority1-Consent-與非醫療提醒主鏈-v1.md](./功能開發/Priority1-Consent-%E8%88%87%E9%9D%9E%E9%86%AB%E7%99%82%E6%8F%90%E9%86%92%E4%B8%BB%E9%8F%88-v1.md)                                        |
| Priority 2 | 真實 AI 食物辨識與候選修正 | V1.X：GPT 辨識已接上，補齊分流、修正體驗與穩定驗收        | [功能開發/Priority2-真實-AI-食物辨識與候選修正-v1.md](./功能開發/Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md)               |
| Priority 3 | 正式營養資料來源與估算策略 | **已完成**：canonical mapping、unit normalization、nutrition source 層級、metadata 可追溯性、history 結果重用均已驗收 | [功能開發/Priority3-正式營養資料來源與估算策略-v1.md](./功能開發/Priority3-%E6%AD%A3%E5%BC%8F%E7%87%9F%E9%A4%8A%E8%B3%87%E6%96%99%E4%BE%86%E6%BA%90%E8%88%87%E4%BC%B0%E7%AE%97%E7%AD%96%E7%95%A5-v1.md) |
| Priority 4 | 前端 IA 與手機體驗補齊     | **已完成**：Landing 產品化、主導覽中文化、re-estimate bottom sheet、文案全面收斂 | [功能開發/Priority4-前端IA與手機體驗補齊-v1.md](./功能開發/Priority4-%E5%89%8D%E7%AB%AFIA%E8%88%87%E6%89%8B%E6%A9%9F%E9%AB%94%E9%A9%97%E8%A3%9C%E9%BD%8A-v1.md)                                         |
| Priority 5 | 觀測性與效能基線           | **已完成**：analysis latency、provider error rate、fallback rate、correction rate 量測均已實作並通過部署後驗收 | [功能開發/Priority5-觀測性與效能基線-v1.md](./功能開發/Priority5-%E8%A7%80%E6%B8%AC%E6%80%A7%E8%88%87%E6%95%88%E8%83%BD%E5%9F%BA%E7%B7%9A-v1.md)                                                        |

### 7.2 Priority 閱讀順序

若你目前最擔心的是「是否往自己不確定的方向前進」，建議閱讀順序如下：

1. 先看 Priority 2 詳細文件，因為 GPT 辨識已接上，下一步核心不確定性主要集中在 partial 判定、candidate review、re-estimate 與穩定驗收
2. 接著看 Priority 3，因為真實辨識接上後，營養資料來源會直接影響結果可信度
3. 再看 Priority 1 與 Priority 4，確認已完成的合規主鏈，以及後續產品體驗如何補齊
4. 最後看 Priority 5，作為部署後持續驗證的量測基線

### Priority 1｜補齊 Consent 與非醫療提醒主鏈

詳見：[功能開發/Priority1-Consent-與非醫療提醒主鏈-v1.md](./功能開發/Priority1-Consent-%E8%88%87%E9%9D%9E%E9%86%AB%E7%99%82%E6%8F%90%E9%86%92%E4%B8%BB%E9%8F%88-v1.md)

### Priority 2｜收斂真實 AI 食物辨識與候選修正

詳見：[功能開發/Priority2-真實-AI-食物辨識與候選修正-v1.md](./功能開發/Priority2-%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98%E8%88%87%E5%80%99%E9%81%B8%E4%BF%AE%E6%AD%A3-v1.md)

### Priority 3｜完善 nutrition source 與 canonical mapping 策略

詳見：[功能開發/Priority3-正式營養資料來源與估算策略-v1.md](./功能開發/Priority3-%E6%AD%A3%E5%BC%8F%E7%87%9F%E9%A4%8A%E8%B3%87%E6%96%99%E4%BE%86%E6%BA%90%E8%88%87%E4%BC%B0%E7%AE%97%E7%AD%96%E7%95%A5-v1.md)

### Priority 4｜補齊 IA 中缺少的前端頁面與手機體驗

詳見：[功能開發/Priority4-前端IA與手機體驗補齊-v1.md](./功能開發/Priority4-%E5%89%8D%E7%AB%AFIA%E8%88%87%E6%89%8B%E6%A9%9F%E9%AB%94%E9%A9%97%E8%A3%9C%E9%BD%8A-v1.md)

### Priority 5｜補觀測性與效能基線

詳見：[功能開發/Priority5-觀測性與效能基線-v1.md](./功能開發/Priority5-%E8%A7%80%E6%B8%AC%E6%80%A7%E8%88%87%E6%95%88%E8%83%BD%E5%9F%BA%E7%B7%9A-v1.md)

---

## 8. 這算不算 PRD v2

目前建議的下一步，原則上不應視為 PRD v2。

原因如下：

1. 這一輪優先項目仍在補齊 [PRD-v1.md](./PRD-v1.md) 已經定義的 MVP 範圍
2. 目前缺的是落地完成度，不是產品方向改版
3. 若現在就另開 PRD v2，容易把 v1 尚未完成的缺口與新需求混在一起

比較準確的說法應是：

1. 這是「PRD v1 gap-closing plan」
2. 或是「PRD v1 下一階段開發優先順序」

只有當團隊決定新增以下類型需求時，才比較像 PRD v2：

1. 每日飲食累積紀錄
2. 手動搜尋完整食物資料庫
3. 更完整的個人目標設定
4. 更多主題模式與無障礙設計
5. 付費方案與進階報表

以上項目已經比較接近 [PRD-v1.md](./PRD-v1.md) 第 16 節的後續階段建議，而不是目前這份文件列出的補齊工作。

---

## 9. 建議的決策方式

這一節處理的是「現在接下來要補哪一個產品缺口」，不是「下一個開發步驟是 Step 幾」。

若下一輪只做一個主題，建議優先選：

1. 真實 AI 食物辨識穩定化與 candidate review 驗收

若下一輪要做一個完整技術主題，建議優先選：

1. GPT / OpenAI 食物辨識的 partial 判定、錯誤分流與最小觀測性

若下一輪要做一個最接近產品價值驗證的組合，建議順序為：

1. Priority 2：真實 AI 食物辨識穩定化與候選修正驗收
2. Priority 3：正式營養資料來源與估算策略
3. Priority 4：前端 IA 補完與手機體驗精修
4. Priority 5：觀測性與效能基線

---

## 10. 建議後續文件分工

若後續要把本文件拆得更細，建議分工如下：

1. PRD 若有產品範圍變更，更新 [PRD-v1.md](./PRD-v1.md) 或另開 `PRD-v2.md`
2. 若只是補齊 v1 未完成項目，本文件保留為總覽與導覽
3. Priority 1 到 Priority 5 的詳細內容，各自維護在 `docs/功能開發/` 下的獨立文件
4. 若要追蹤 Step 2 的歷史工作包、Ticket 與驗收矩陣，維持 [setup/Step2-核心開發任務清單-v1.md](./setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md)
5. 若要查看 CI/CD 與 AWS 部署維護事項，回到 `docs/setup/` 下對應文件，不再把它們寫進 Priority 詳細文件
