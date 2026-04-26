# Priority 2｜真實 AI 食物辨識與候選修正 v1

- 文件名稱：Priority 2｜真實 AI 食物辨識與候選修正
- 版本：v1
- 日期：2026-04-26
- 狀態：Draft
- 用途：把真實 AI 辨識主鏈、candidate confirmation 與 fallback 補成可追蹤的開發主題

---

## 1. 文件定位

本文件處理的是 PRD v1 gap-closing plan 中的 Priority 2。

這是目前最接近 HappyMeal 核心產品價值的主題，也是最容易讓開發方向變得模糊的區塊，因此需要比總覽文件更細的拆解。

---

## 2. 為什麼這份文件要拆細

Priority 2 同時牽涉：

1. AI provider 接入
2. 後端辨識邊界與 fallback
3. 候選修正 UI
4. confirm 與 nutrition estimate 的契約
5. 後續 re-estimation 與觀測性

若只放在總覽文件裡，容易讓人分不清：

1. 哪些是已經開始做的
2. 哪些只是方向，不是當前切片
3. 哪些屬於下一階段，而不是這一輪要一起做完

---

## 3. 目前狀態

目前可視為已知進度如下：

1. analysis upload -> recognition provider -> normalization 的後端邊界已開始形成
2. OpenAI 單一 provider 路徑已接入
3. confirm 已從「不在白名單就 400」改成較可完成的 fallback 路徑
4. candidate review UI 已開始補可改單位、刪除誤判、手動新增食物
5. 圖片上傳後的辨識流程，已開始把「AI 可恢復失敗」和「真正請求錯誤」分開處理；當 AI 發生可恢復失敗時，系統已可改為導向手動修正，而不是直接把整條主鏈中止

目前仍未完成的重點：

1. 真實圖片辨識的失敗收尾雖然已開始收斂，但仍需要持續補齊更多實際情境與驗證，例如不同類型的 provider 失敗、候選為空時的使用者理解、以及部署環境中的穩定度觀察。這一段還要補，是為了把「可手動繼續」從第一版能力，收斂成真正可依賴的主鏈行為。
2. candidate review 還需要完整手動驗證，因為 UI 雖然已補上改名稱、改份量、改單位、刪除與新增，但還需要實際用真實流程確認手機上是否真的順手、會不會有漏掉的卡點。這一段要補，是為了確認「AI 不準也能靠人工完成」不是只停留在程式碼層面。
3. 「再次請 AI 估算」還沒做成正式功能，因為目前使用者修改候選後，系統還不能把新內容再交給 AI 做第二次推估。這一段要補，是為了提升修正效率，但它屬於第二階段增強，不是先讓主鏈可完成的必要條件。
4. 最小觀測性還沒補齊，因為現在多半還是靠人工看 log 才知道 provider 是 timeout、配額不足還是圖片資料錯誤。這一段要補，是為了讓後續調 prompt、換模型或排錯時，有基本數據可以看，不用每次都靠猜。

---

## 4. 目標

讓使用者在真實圖片上傳後，即使 AI 辨識不準，也能在同一條主鏈內完成：

1. 取得候選食物
2. 手動修正名稱、份量與單位
3. 刪除誤判與手動新增漏掉的食物
4. 完成 confirm，而不被 provider 或 rigid contract 卡住

---

## 5. 工作拆解

### P2-01 辨識邊界與單一 provider

目標：先把真實圖片主鏈打通，而不是一開始追求多 provider。

包含：

1. upload service 與 provider 邊界
2. 單一 provider 接入
3. 最小可用 prompt
4. normalization 與 candidate response

### P2-02 provider fallback 與 manual_required

目標：AI 不穩時，主鏈仍可走完。

包含：

1. timeout 處理
2. provider error handling
3. manual_required 或等價 fallback
4. 不讓使用者因為辨識失敗直接中斷整條流程

### P2-03 Candidate Confirmation 修正體驗

目標：把「辨識普通但手動修正非常順」做完整。

包含：

1. 編輯名稱
2. 調整份量
3. 調整單位
4. 刪除誤判
5. 手動新增項目

### P2-04 confirm 與營養估算契約

目標：讓 confirm 不再與 rigid food whitelist 綁死。

包含：

1. fallback-friendly contract
2. metadata 與估算來源
3. 盡量以 g 作為計算基準

### P2-05 re-estimation 能力

目標：在 candidate review 可用後，再補第二層效率工具。

包含：

1. 使用者修改後再次請 AI 估算
2. 不直接覆蓋使用者最後輸入
3. 保留人類最終確認權

### P2-06 最小觀測性

目標：讓後續調 prompt、模型與 provider 時有可讀依據。

包含：

1. latency
2. timeout
3. error rate
4. manual fallback rate
5. correction rate
6. re-estimation usage rate

### 目前程式實作規劃

目前這條主線的實作規劃，以「provider 失敗不等於主鏈失敗」為核心，分成 4 個責任層來收斂：

1. 先整理 AI provider 的失敗類型，讓系統能分辨哪些屬於可恢復失敗，哪些屬於真正不合法的請求
2. 再把辨識結果改成可表達狀態的結果物件，而不是只回傳候選清單，讓後續流程能分辨成功候選、無可靠候選、可手動繼續的 fallback
3. 接著讓圖片上傳回應能直接帶出 fallback 狀態與提示訊息，避免前端只能靠候選是否為空來猜目前發生了什麼事
4. 最後由前端承接這些狀態：若屬於可手動繼續的情況，就直接進入 candidate review，並用低噪音提示告訴使用者可以繼續手動調整

目前這 4 層中的第一階段已開始落地，重點是先把可恢復失敗從一般 500 錯誤中分離出來，讓使用者不會因為 AI 一次不穩就整條流程中止。

### 完成後如何更新文件

後續每完成一段程式調整並通過對應驗證後，應同步回寫這份文件的三個地方：

1. `目前可視為已知進度如下`：補上這次已經落地的能力
2. `目前仍未完成的重點`：移除已完成項目，或改寫成剩餘風險
3. `目前程式實作規劃`：標記哪一段已開始落地，哪一段仍在後續階段

原則是：已完成的內容要搬到進度區，不要一直停留在規劃區；這樣文件才不會落後於實作。

---

## 6. 推進順序

建議順序如下：

1. 先讓真實圖片候選主鏈可回傳 candidate
2. 再補 provider timeout、error handling 與 fallback
3. 接著把 candidate confirmation 的修正能力做順
4. 然後收斂 confirm 與 nutrition contract
5. 最後再補 re-estimation 與觀測性

這個順序的理由是：

1. 使用者能不能把流程走完，比單次辨識準不準更重要
2. 若 candidate review 還不順，太早補 re-estimation 只會增加混亂
3. 若沒有觀測性，後續 prompt 與 provider 調整會失去判斷依據

---

## 7. 明確不做

1. 多 provider 切換平台
2. 完整食物資料庫搜尋
3. 一開始就追求極致辨識準確率
4. 把 AI 估出的營養值直接當唯一真相

---

## 8. 驗收條件

1. `/analyses/{id}/image` 可從真實圖片回傳 candidate
2. provider 不穩時，使用者仍可透過 fallback 完成流程
3. candidate review 至少支援編輯名稱、份量、單位、刪除與新增項目
4. confirm 不會再因 rigid whitelist 或 rigid unit contract 導致主鏈中斷
5. 至少有最小量測可觀察 timeout、error 與 manual fallback

---

## 9. 相關文件

1. 總覽： [../PRD-實作進度與下一步-v1.md](../PRD-%E5%AF%A6%E4%BD%9C%E9%80%B2%E5%BA%A6%E8%88%87%E4%B8%8B%E4%B8%80%E6%AD%A5-v1.md)
2. 真實 AI 細規格： [真實-AI-食物辨識-MVP-規格-v1.md](./%E7%9C%9F%E5%AF%A6-AI-%E9%A3%9F%E7%89%A9%E8%BE%A8%E8%AD%98-MVP-%E8%A6%8F%E6%A0%BC-v1.md)
3. Step 2 邊界： [../setup/Step2-核心開發任務清單-v1.md](../setup/Step2-%E6%A0%B8%E5%BF%83%E9%96%8B%E7%99%BC%E4%BB%BB%E5%8B%99%E6%B8%85%E5%96%AE-v1.md)
