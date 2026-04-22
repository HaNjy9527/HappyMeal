# HappyMeal PRD 實作進度與下一步 v1

- 文件名稱：HappyMeal PRD 實作進度與下一步
- 版本：v1
- 日期：2026-04-20
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
3. 目前最明確已完成的項目是 LINE Login、Profile、Theme、Consent API、Analysis 主鏈、History 主鏈與後端測試骨架
4. 目前最明確未做滿的項目是真實 AI 食物辨識、正式營養資料來源、Consent Intro 與非醫療提醒覆蓋、以及 IA 中較完整的頁面體驗

---

## 4. PRD 功能對照表

| PRD 項目 | 功能名稱              | 目前狀態 | 目前判讀                                                                                                            | 備註                                                  |
| -------- | --------------------- | -------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| FR-01    | LINE Login 註冊與登入 | 已完成   | 後端已具備 LINE OAuth、callback、signed token exchange、session、`/auth/me`、logout；前端也已串登入頁與受保護頁流程 | 目前可視為已完成                                      |
| FR-02    | 個人資料管理          | 已完成   | 已支援 profile 讀取與更新，包含 age、height、weight、activity、goal、goal weight                                    | 已能支撐 recommendation                               |
| FR-03    | 拍照與圖片上傳        | 部分完成 | 已支援 JPG、PNG 上傳與大小限制，並在完成後刪除暫存圖片                                                              | 手機相機體驗與前端流程仍屬最小版                      |
| FR-04    | 食物辨識              | 部分完成 | 候選結果流程已存在，但目前仍是 mock candidate preset，不是真實 AI provider                                          | 主鏈可驗證，但不算正式完成                            |
| FR-05    | 手動修正與份量確認    | 已完成   | 前端可修改 food name 與 portion，後端可接收 confirm 結果並寫入 item                                                 | 已可完成候選確認                                      |
| FR-06    | 營養估算              | 部分完成 | 可計算 kcal、protein、fat、carb 並回傳總和與明細，但目前來自 preset mapping，不是正式 nutrition source              | 能展示結果，但資料來源仍需升級                        |
| FR-07    | 增肌／減脂建議        | 已完成   | 已依 profile 與 goal 產生 target calories、macro 與推薦運動，語氣仍維持 wellness guidance                           | 已能形成 MVP 第一層建議                               |
| FR-08    | 熱門運動熱量消耗      | 部分完成 | 已有 20 筆 ExerciseCatalog seed，confirm 後可推薦 3 個運動並估算消耗                                                | 尚未形成獨立查詢頁或完整查詢體驗                      |
| FR-09    | 分析歷史              | 已完成   | 已有 history list 與 detail，且回傳建議快照，不保存原始圖片                                                         | 符合主鏈需求                                          |
| FR-10    | 主題切換              | 部分完成 | theme_preference 已可跨裝置保存，前端亦可切換兩種主題                                                               | 目前偏最小版，尚未發展成完整 Theme Preference 頁      |
| FR-11    | 同意與聲明            | 部分完成 | Consent API 與資料保存已完成                                                                                        | 前端尚未完成首次 Consent Intro 與全流程非醫療提醒覆蓋 |

---

## 5. 驗收條件對照表

| 驗收條件                                         | 目前狀態 | 判讀                                                                         |
| ------------------------------------------------ | -------- | ---------------------------------------------------------------------------- |
| 使用者可在手機完成登入、建檔、拍照分析與查看建議 | 部分完成 | 主鏈已存在，但手機優先體驗仍偏最小實作，Consent Intro 與完整 Home 體驗未補齊 |
| AI 辨識失準時，使用者可手動修正後完成流程        | 已完成   | 雖然辨識來源仍是 mock，但手動修正與 confirm 主鏈已可操作                     |
| 歷史紀錄可查看過去分析摘要與建議快照             | 已完成   | history list 與 detail 已具備                                                |
| 系統不長期保存原始圖片                           | 已完成   | analysis 完成後會刪除暫存圖片                                                |
| 主題切換後重新登入仍保留偏好                     | 部分完成 | 偏好保存已完成，但仍建議補實際跨裝置手動驗收紀錄                             |
| 所有建議相關頁面皆顯示非醫療用途提醒             | 尚未完成 | repo 內已有 consent 能力，但前端畫面提醒覆蓋仍不足                           |

---

## 6. 與 Step 2 的關係

目前狀態可以概括為：

1. Step 2 的最小主流程驗證已大致達標
2. 但 Step 2 的完成，不等於 PRD v1 的完整 MVP 體驗完成
3. 目前差距主要集中在「正式能力」與「使用者可見流程補齊」，而不是基礎 CRUD 或資料模型

最重要的落差如下：

1. mock candidate 尚未替換成真實 AI 食物辨識
2. preset nutrition 尚未替換成正式營養資料來源
3. Consent Intro、免責聲明、Landing / Home / Theme 等 IA 頁面仍偏最小版
4. 手機優先體驗雖可用，但仍未精修成 PRD 描述的產品感受

---

## 7. 下一個開發優先順序

本節的目的不是擴張新需求，而是先補齊 PRD v1 尚未完成的缺口。

### Priority 1｜補齊 Consent 與非醫療提醒主鏈

目標：先把合規與使用者可見流程補完整。

原因：

1. FR-11 與驗收條件第 6 點目前還沒有真正完成
2. Consent API 已存在，補前端成本低，卻能直接讓 MVP 更接近 PRD 驗收
3. 這屬於既有主鏈補完，不是新範圍擴張

建議包含：

1. 首次登入後進入 Consent Intro，而不是直接視為流程已完成
2. 在 Analysis Result、History Detail、相關建議區塊補上非醫療用途提醒
3. 補上 consent 狀態檢查，避免未同意就進入建議流程
4. 建立正式上線文案稿，並同步到 Consent Intro 畫面
5. 新增兩個必要 checkbox，兩者皆勾選後才可按下「同意並繼續」
6. 讓 Consent 文案區塊可收合，降低手機閱讀壓力

### Priority 2｜把 mock 食物辨識替換成真實 AI provider

目標：讓 FR-04 從「可演示」升級到「可驗證真實產品價值」。

原因：

1. 目前 analysis 主鏈雖然能跑通，但核心產品價值仍建立在 mock candidate 上
2. 若沒有真實辨識，PRD 成功指標中的分析成功率與手動修正率無法被真正驗證
3. 這是最接近 HappyMeal 核心價值主張的功能缺口

建議包含：

1. 抽象化 analysis upload / recognition provider 邊界
2. 接上單一 AI provider 即可，不必一開始就做多 provider 切換
3. 補 timeout、error handling、fallback 與耗時記錄
4. 補上「使用者修正後再次請 AI 協助估算」的互動與 API 邊界，但最終確認權仍由使用者保留

目前建議的落地方向：

1. 第一版 provider 優先採 OpenAI，模型首選 `GPT-5.4 mini`
2. 第一版重點不是追求單次辨識極致準確，而是把「辨識普通但手動修正非常順」做完整
3. 支援整份餐點中的多個食物，並盡量涵蓋台灣日常飲食與可辨識飲料
4. 營養結果仍應由正式 nutrition source 或內部 mapping 計算，不直接相信 AI 估出的營養數值
5. 若 AI 辨識不足，應以 `manual_required` 或同等 fallback 方式讓使用者在同一主鏈完成補輸入
6. 月預算若僅約新台幣 `200` 元，較適合 PoC 或少量封測，不適合作為真實使用者規模的長期月預算假設

推薦的執行優先順序：

1. 先抽出 `analysis upload -> recognition provider -> normalization` 的後端邊界，避免後續直接把 OpenAI 細節寫死在 upload service 內
2. 先接上單一 provider 與最小可用 prompt，讓 `/analyses/{id}/image` 能從真實圖片回傳 candidate，而不是先花時間做多 provider 或過度抽象化
3. 優先補 `manual_required`、timeout、provider error handling，確保 AI 不穩時主鏈仍可走完
4. 接著補前端 Candidate Confirmation 的順手修正能力，至少包含編輯名稱、調整份量、刪除誤判與補新增食物
5. 在 Candidate Confirmation 可用後，再補「再次請 AI 估算」能力，讓使用者修改內容後可請 AI 重新推估候選與份量，但不直接覆蓋使用者最後輸入
6. 再補最小觀測性，先記錄 latency、timeout、error rate、manual fallback rate、correction rate 與 re-estimation 使用率
7. 最後才根據真實照片與 correction data，調整 prompt、模型等級或是否要更換 provider

這個順序的理由是：

1. 先把技術邊界切乾淨，後面才不會因為換模型或補 fallback 造成大面積重寫
2. 先讓真實圖片主鏈跑通，比提早優化準確率或提早做監控儀表板更有驗證價值
3. 在 HappyMeal 的前提下，AI 不完美是可接受的，但不能讓使用者卡住，因此 fallback 與修正體驗應早於精修模型表現
4. 「再次請 AI 估算」屬於加強修正效率的第二層能力，應建立在基本修正體驗已可用的前提上，否則只會增加複雜度而不穩定

相關詳細規格請見：[功能開發/真實-AI-食物辨識-MVP-規格-v1.md](./功能開發/真實-AI-食物辨識-MVP-規格-v1.md)

### Priority 3｜把 preset 營養估算替換成正式 nutrition source

目標：讓 FR-06 與 FR-07 的結果從 demo 級提升到可持續使用的 MVP 級。

原因：

1. 目前 totals 正確性只對 preset 食物成立
2. 真實辨識接上後，若營養來源仍是硬編碼，結果品質仍不足
3. 這一層完成後，history 與 recommendation 的資料才有真正價值

建議包含：

1. 建立 normalized food name 到 nutrition data 的 mapping 策略
2. 保留估算值標示
3. 避免一開始就擴成完整手動搜尋食物資料庫

### Priority 4｜補齊 IA 中缺少的前端頁面與手機體驗

目標：把最小主流程殼補成較接近 PRD 的可用產品。

建議包含：

1. 補強 Landing Page 產品價值與免責說明
2. 補出更完整的 Home Dashboard，而不是只依賴 tab 化主流程頁
3. 補 Theme Preference 與 Consent Review 的明確頁面結構
4. 依 [IA-User-Flows-v1.md](./IA-User-Flows-v1.md) 補齊錯誤、空狀態與內容策略

### Priority 5｜補觀測性與效能基線

目標：為正式 AI provider 與後續部署驗收準備基礎量測。

建議包含：

1. 記錄 analysis 耗時、provider timeout、error rate
2. 對照 [部署與用量預估-v1.md](./%E9%83%A8%E7%BD%B2%E8%88%87%E7%94%A8%E9%87%8F%E9%A0%90%E4%BC%B0-v1.md) 的監控建議補最小指標
3. 讓後續 Step 4 / Step 5 與真實流量驗收更可判讀

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

若下一輪只做一個主題，建議優先選：

1. Consent 與非醫療提醒主鏈補齊

若下一輪要做一個完整技術主題，建議優先選：

1. 真實 AI 食物辨識 provider 接入

若下一輪要做一個最接近產品價值驗證的組合，建議順序為：

1. Consent 與免責聲明補齊
2. 真實 AI 食物辨識
3. 正式營養資料來源
4. 前端 IA 補完與手機體驗精修

---

## 10. 建議後續文件分工

若後續要把本文件拆得更細，建議分工如下：

1. PRD 若有產品範圍變更，更新 [PRD-v1.md](./PRD-v1.md) 或另開 `PRD-v2.md`
2. 若只是補齊 v1 未完成項目，可維持本文件作為進度盤點
3. 若要排票與驗收，更新 [setup/Step2-核心開發任務清單-v1.md](./setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md) 或另開下一階段 backlog 文件
