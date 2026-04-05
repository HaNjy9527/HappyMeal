# HappyMeal 部署排錯紀錄 v1

- 文件名稱：部署與登入流程排錯紀錄
- 版本：v1
- 日期：2026-04-05
- 狀態：已結案
- 用途：記錄 LINE Login + AWS Lightsail + Vercel 部署過程中遇到的問題、處理方式與學到的教訓，供後續開發借鑑

---

## 概覽

本次完成的工作範圍為：
- Step 5（LINE Login 後端 auth/session 實作）
- Step 6、7（前端 routing、auth hooks、cookie 串接）
- AWS Lightsail + Vercel 首次正式部署與打通

主要排錯期間共遇到 8 個獨立問題，按發生順序整理如下。

---

## 問題 1：前端打登入按鈕後 URL 變成 localhost

**現象**
按下 LINE 登入按鈕後，請求的 URL 是 `http://localhost:8000/auth/line/login`，無法在正式環境打通。

**根本原因**
Vite 的環境變數是 **build time** 寫死進 bundle，不是 runtime 讀取。前端讀取 `VITE_BACKEND_URL`（當時的舊變數名），若 build 時沒有這個值，會退回 fallback `http://localhost:8000`。因為 fallback 存在，build 不會報錯，直到上線才會暴露。

加上這個變數之前被改名過（從 `VITE_API_BASE_URL` 改成 `VITE_BACKEND_URL`），而 Vercel 的 Environment Variables 還停留在舊名稱，導致 build 拿不到值。

**處理方式**
1. 決定把環境變數名稱改回 `VITE_API_BASE_URL`，避免新舊混用。
2. Vercel 的 Environment Variables 要設 `VITE_API_BASE_URL`，不是放進 GitHub Secrets。
3. 設完後重新部署前端（Vercel 才會用新值跑 build）。

**教訓**
- Vite 環境變數要去 Vercel 設，不是 GitHub Secrets。
- 有 fallback 不代表沒問題，只代表問題會延遲到上線才爆。
- 改環境變數名稱時，必須一次同步：程式碼、.env.example、docker-compose、Vercel env、所有相關文件。

---

## 問題 2：不必要的環境變數改名（`AI_API_KEY` → `AI_FOOD_API_KEY`）

**現象**
整理環境變數時發現 GitHub Secrets 裡有 `AI_API_KEY`，但 workflow 和程式碼已被改成 `AI_FOOD_API_KEY`，造成不一致。

**根本原因**
先前進行環境變數整理時，改了 AI 相關 key 的名稱，但沒有充分評估必要性。產品目前只有一個 AI 服務，不需要為了「可能的未來擴充」現在就改名。

**處理方式**
把 `AI_FOOD_API_KEY` 全部改回 `AI_API_KEY`，影響範圍：`config.py`、`.env.example`、`ci.yml`、相關 setup 文件。

**教訓**
- 環境變數改名的收益通常低於成本（部署同步問題）。
- 除非有明確的新需求（例如真的要接第二個 AI 服務），否則不要主動改名。
- 改名的標準：「現在不改，之後真的會很麻煩」，而不是「未來可能需要」。

---

## 問題 3：GitHub Actions CD 的 JSON 格式錯誤

**現象**
```
Error: aws: [ERROR]: An error occurred (ParamValidation): Error parsing parameter '--containers': Invalid JSON
```

**根本原因**
Lightsail `--containers` 參數需要合法 JSON，但 workflow 裡被注入的環境變數（來自 GitHub Secrets）有些 key 沒有雙引號包裹，形成非法 JSON。具體是這樣的：
```
APP_ENV: production,       ← key 沒有引號
LINE_CALLBACK_URL: ***,    ← key 沒有引號
```

**處理方式**
把 `ci.yml` 裡 `--containers` 的 JSON 改成全部使用統一的 escaped JSON 格式，確保 key 和 value 都有雙引號。

**教訓**
- YAML 裡嵌 JSON 很容易出現引號混亂，建議測試時先把 workflow echo 出來看實際被拼出的字串是什麼。
- GitHub Secrets 的值在 workflow log 裡會被 `***` 遮蔽，難以直接除錯，所以 JSON 結構要靠 workflow 本身保證。

---

## 問題 4：`FRONTEND_URL` 和 `LINE_CALLBACK_URL` 的差異混淆

**現象**
在設定時搞不清楚這兩個是什麼、為什麼都要設、設在哪裡。

**釐清結果**

| 變數 | 說明 | 值的格式 |
|---|---|---|
| `LINE_CALLBACK_URL` | LINE 授權完成後，LINE 伺服器要打回哪個**後端 endpoint** | `https://backend-url/auth/line/callback` |
| `FRONTEND_URL` | 後端建立 session 之後，要把使用者送去哪個**前端頁面** | `https://frontend-url`（不含路徑） |

完整 OAuth 流程：
```
前端按登入
  → backend /auth/line/login
    → LINE 授權頁
      → LINE_CALLBACK_URL（backend /auth/line/callback）
        → backend 建立 session
          → FRONTEND_URL + /home
```

`LINE_CALLBACK_URL` 是中繼站（backend 處理 OAuth），`FRONTEND_URL` 是最終目的地（前端 UI）。

**教訓**
- OAuth 流程有兩段 redirect，一定要分清楚。第一段給第三方服務（LINE），第二段給自己的前端。
- 如果把 `FRONTEND_URL` 設成 backend domain，登入後就會把使用者導到 Lightsail URL，而不是 Vercel 前端。

---

## 問題 5：`redirect_uri` 空白導致 LINE 400

**現象**
按下登入後，LINE 回報：
```
Confirm your request. redirect_uri parameter is blank.
```

LINE 授權 URL 裡出現 `redirect_uri=`（空值）。

**根本原因**
Backend 在組 LINE authorize URL 時，`settings.line_callback_url` 是空字串。Backend 可以正常啟動（因為這個欄位沒有設成必填），但等到真正呼叫 `/auth/line/login` 時才會炸。

直接原因是 GitHub Secrets 裡的 `LINE_CALLBACK_URL` 沒有建立，或 workflow 沒有把它注入 Lightsail，導致 backend runtime 讀不到值。

**處理方式**
1. 確認 GitHub Secrets 有 `LINE_CALLBACK_URL`。
2. 確認 `ci.yml` 的 deploy 步驟有把這個 secret 注入 Lightsail environment。
3. 重新部署 backend。

**教訓**
- 若 secret 有設但 workflow 沒注入，效果等於沒設。要同時檢查 GitHub Secrets 和 workflow 的 `--containers` 環境變數清單。
- 沒有設必填驗證的設定值，啟動不會失敗，排查更困難。重要的設定值應考慮在 startup 時做驗證。

---

## 問題 6：LINE OAuth `state` 驗證失敗（Invalid state parameter）

**現象**
LINE 帶著 `code` 和 `state` 回到 callback，但 backend 回應 400：
```json
{"detail": "Invalid state parameter"}
```

**根本原因**
原本的 auth 實作把 `oauth_state` 存進 backend session cookie，再在 callback 時從 session 取出比對。但在跨 domain（前端 Vercel、backend Lightsail）或特定瀏覽器環境下，callback 那一刻可能讀不到原本那份 session，導致 state 比對失敗。

**處理方式**
改成「state 帶簽章」的容錯機制：
1. 產生 `state` 時，同時用 `itsdangerous` 做 HMAC 簽章。
2. Callback 時優先比對 session。
3. 若 session 遺失，仍可用簽章驗證 state 是否為系統簽發且未過期。

**教訓**
- 純靠 session 存 state 在跨 domain 部署下不穩定，特別是 SameSite cookie 限制可能導致 session 不跟著帶過去。
- OAuth state 驗證應兼具 session 比對和簽章驗證兩層。
- 這是 LINE Login 搭配前後端分離部署時的常見陷阱。

---

## 問題 7：前端 redirect 網址前有空白（`/%20https://...`）

**現象**
登入成功後，瀏覽器被導到奇怪的 URL：
```
https://backend-url/auth/line/ https://frontend-url/home
```

**根本原因**
GitHub Secret `FRONTEND_URL` 的值前面或後面有空白字元（例如複製時多帶了空格）。Backend 把這個值直接拼進 redirect URL 時，瀏覽器把 `%20https://...` 解讀成相對路徑，而不是絕對 URL。

**處理方式**
1. 短期：在 `config.py` 對所有 URL 類型的環境變數做 `strip()`。
2. 同時：手動重新輸入 GitHub Secrets 的值，確認沒有前後空白。

**教訓**
- 從 Lightsail Console 或 GitHub Secrets 複製值時，很容易帶入不可見的空白字元。
- 程式碼層面應對 URL 類的環境變數做防呆 `strip()`。
- 遇到 URL 格式異常，先直接印出實際 redirect target，確認是哪個值出問題。

---

## 問題 8：進入 `/home` 直接顯示 Vercel 404

**現象**
LINE 登入成功後被導到 `https://happy-meal-three.vercel.app/home`，但頁面顯示 `404: NOT_FOUND`。

**根本原因**
React 的 `/home` 是前端 client-side route，不是靜態檔案。Vercel 收到直接請求 `/home` 時，找不到對應的靜態檔案，就回 404。需要 Vercel 的 SPA rewrite 設定，把所有路由都轉到 `index.html`，讓 React Router 接管。

**處理方式**
在 `frontend/vercel.json` 加入 rewrite 設定：
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

**教訓**
- React SPA 部署到 Vercel（或任何靜態站點）時，一定要加 `vercel.json`（或對應的 rewrite 設定），否則 client-side route 直連或刷新都會 404。
- 這是 SPA 部署常見的基礎設定，但容易被遺漏。

---

## 附錄 A：環境變數設定位置總覽

| 變數 | 設在哪裡 | 說明 |
|---|---|---|
| `VITE_API_BASE_URL` | **Vercel** Environment Variables | 前端 build time 注入，必須設在 Vercel，不是 GitHub Secrets |
| `LINE_CALLBACK_URL` | GitHub Secrets + workflow 注入 Lightsail | Backend OAuth callback URL |
| `FRONTEND_URL` | GitHub Secrets + workflow 注入 Lightsail | Backend 登入完成後導回的前端 URL |
| `LINE_CHANNEL_ID` | GitHub Secrets + workflow 注入 Lightsail | LINE Login Channel ID |
| `LINE_CHANNEL_SECRET` | GitHub Secrets + workflow 注入 Lightsail | LINE Login Channel Secret |
| `SESSION_SECRET_KEY` | GitHub Secrets + workflow 注入 Lightsail | Session 簽章金鑰 |
| `DATABASE_URL` | GitHub Secrets + workflow 注入 Lightsail | PostgreSQL 連線字串 |
| `AI_API_KEY` | GitHub Secrets + workflow 注入 Lightsail | AI 食物辨識 API 金鑰 |
| `CORS_ALLOW_ORIGINS` | GitHub Secrets + workflow 注入 Lightsail | 允許的前端 origin，直接填 URL，不含方括號 |
| `APP_ENV` | workflow 直接寫（值為 `production`） | 不需要設進 Secrets |

**重要：Vercel 的環境變數和 GitHub Secrets 是兩個完全不同的地方。** 前端的 Vite 環境變數只能從 Vercel 設，GitHub Secrets 設了沒用。

---

## 附錄 B：LINE Login 兩段 Redirect 快速參考

```
LINE_CALLBACK_URL
= https://[lightsail-backend-domain]/auth/line/callback
  ↑ LINE 用這個打回後端

FRONTEND_URL
= https://[vercel-frontend-domain]
  ↑ 後端用這個 + "/home" 把使用者送回前端
```

---

## 附錄 C：CI/CD 觸發規則（整理後）

目前 GitHub Actions 只在 `backend/**` 有變動時觸發：
- 改後端：GitHub Actions 跑 backend test + Lightsail deploy。
- 改前端：Vercel 自動偵測 GitHub push，跑 frontend build + 部署。
- 改文件：兩邊都不觸發部署。

前端 Docker image 不再是部署鏈的一部分（仍保留供本機開發使用）。
