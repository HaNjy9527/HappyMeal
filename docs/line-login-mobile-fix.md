# LINE Login 手機登入狀態修復說明

## 問題描述

在手機裝置上完成 LINE Login 後，使用者仍會看到登入按鈕（登入狀態未保存）。

### 根本原因：跨 context Cookie 無法共享

手機上的 LINE OAuth 流程如下：

```
使用者瀏覽器 (Safari / Chrome)
  → 點擊登入按鈕
  → 後端設定 oauth_state session cookie，redirect 至 LINE OAuth URL

LINE OAuth 偵測到裝置有 LINE app
  → 開啟 LINE app 完成授權

LINE app 完成後 redirect 到 callback URL
  → 在 LINE 內建 WebView 或 Chrome Custom Tab 執行
  ↑ 這個 context 有獨立的 Cookie Jar，與使用者原本的瀏覽器 tab 不共享

後端 /auth/line/callback（在 LINE 的 context 中執行）
  → 原本：設定 user_id session cookie → redirect 到 /home
  → 問題：這個 cookie 被存在 LINE 的 context，不在使用者的瀏覽器

系統瀏覽器另開新頁顯示 /home
  → 沒有 session cookie → /auth/me 回傳 401 → 顯示登入按鈕
```

## 解決方案：短效簽名 Token in URL

修改 callback 的行為：不直接設定 session cookie，而是產生一個短效的簽名 token，
放在 redirect URL 的 query string 中。前端（在使用者的實際瀏覽器中）讀到 token 後，
呼叫新的 exchange 端點，由後端在**正確的瀏覽器 context** 設定 session cookie。

### 新流程

```
LINE callback（在 LINE 的 WebView 中）
  → 後端驗證 OAuth、建立或更新 User
  → 產生短效簽名 token（2 分鐘有效期）
  → 302 redirect 到 /?token=<signed_token>    ← 不設定 session cookie

使用者的實際瀏覽器開啟 /?token=xxx（新 tab）
  → LandingPage useEffect 偵測到 ?token= 參數
  → POST /auth/exchange-token { token }        ← 在正確的瀏覽器 context 發出
  → 後端驗證 token，設定 session["user_id"]    ← cookie 設在正確的 context
  → 前端 invalidate ["me"] query → 重新 fetch /auth/me → 200
  → 使用者已登入 → auto-redirect 到 /home
```

## 實作變更

### 後端

**`backend/app/services/auth.py`**

- 新增 `AUTH_TOKEN_MAX_AGE_SECONDS = 120`（2 分鐘）
- 新增 `build_auth_token_signer()` — 使用 `salt="line-auth-token"`，與 OAuth state signer 隔離
- 新增 `create_auth_token(user_id, settings)` — 簽名並回傳 token 字串
- 新增 `verify_auth_token(token, settings)` — 驗證簽名與有效期，回傳 user_id
- 更新 `build_frontend_redirect_url()` — 新增 `token` 參數支援

**`backend/app/api/routes/auth.py`**

- 修改 `GET /auth/line/callback`：改為產生 auth token 並 redirect 到 `/?token=...`，**不再設定 session**
- 新增 `POST /auth/exchange-token`：驗證 token、查詢 User、設定 `session["user_id"]`，回傳 `AuthMeResponse`

### 前端

**`frontend/src/api.ts`**

- 新增 `exchangeAuthToken(token)` — POST 到 `/auth/exchange-token`

**`frontend/src/App.tsx`（LandingPage）**

- 讀取 URL 中的 `?token=` 參數
- `useEffect` 偵測到 token 時：呼叫 exchange → 清除 URL 中的 token → invalidate React Query cache
- 在 exchange 期間顯示 loading 畫面
- token 失效時顯示錯誤提示

## 安全性

| 屬性              | 說明                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------ |
| 無法偽造          | Token 以伺服器 `SESSION_SECRET_KEY` + `itsdangerous` 簽名                                  |
| 有效期限制        | 2 分鐘 TTL，超時後 `verify_auth_token` 拋 400                                              |
| 傳輸安全          | Token 在 HTTPS URL 中，受 TLS 保護                                                         |
| 清除 URL          | 前端 exchange 成功後立即以 `setSearchParams({}, { replace: true })` 清除，不留在瀏覽器歷史 |
| 無需 DB migration | 複用既有的 `TimestampSigner` 模式，不新增 table                                            |

> **注意**：2 分鐘 TTL 代表在 LINE 導回瀏覽器後，使用者有 2 分鐘的時間完成 exchange。
> 若需要更嚴格的一次性 token（完全防 replay），可改為在 DB 記錄已使用的 token，
> 但對於目前的使用情境，2 分鐘 TTL 已足夠安全。

## 測試

`backend/tests/test_auth.py` 涵蓋以下情境：

| 測試                                                  | 說明                                                                          |
| ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| `test_auth_flow_creates_session_and_logout_clears_it` | 完整流程：callback redirect 含 token → exchange → /auth/me 200 → logout → 401 |
| `test_get_line_callback_updates_existing_user`        | callback redirect 改為含 token 的 `/`                                         |
| `test_exchange_token_success`                         | 有效 token → 200 + session 建立                                               |
| `test_exchange_token_expired`                         | 過期 token → 400                                                              |
| `test_exchange_token_invalid`                         | 格式錯誤 token → 400                                                          |

## 手機實機排查清單

這份清單的目的，是在不先改程式碼的前提下，快速判斷問題落在以下哪一層：

1. LINE OAuth callback 本身失敗
2. 前端沒有成功呼叫 `POST /auth/exchange-token`
3. `exchange-token` 成功，但 session cookie 沒被瀏覽器保存
4. 環境變數或部署 URL 指錯站點

### 先確認正式環境 URL

排查前先確認目前正式環境使用的是下列 URL：

1. Frontend URL：`https://happy-meal-three.vercel.app/`
2. Backend URL：`https://happymeal-backend.zyaqqxanc0frj.ap-northeast-1.cs.amazonlightsail.com/`
3. LINE Callback URL：`https://happymeal-backend.zyaqqxanc0frj.ap-northeast-1.cs.amazonlightsail.com/auth/line/callback`

若任一平台設定不是這組值，先修正設定，再做後續排查。

### 檢查步驟

1. 使用 iPhone Safari 開啟前端首頁。
2. 點擊 LINE Login，完成授權。
3. 觀察導回後的網址是否短暫出現 `?token=`。
4. 若完全沒有看到 `?token=`，優先檢查 callback redirect 與 `FRONTEND_URL`。
5. 若有看到 `?token=`，但很快又回到登入按鈕，代表前端至少有機會進入 token handoff 流程。

### 用 Safari Web Inspector 看網路請求

若手邊有 Mac，可以直接用 Safari Web Inspector 檢查：

1. iPhone 到「設定 > Safari > 進階」開啟 Web Inspector。
2. 用傳輸線把 iPhone 接到 Mac。
3. Mac Safari 到「Settings > Advanced」開啟 Show Develop menu。
4. 在 iPhone Safari 重新操作一次登入。
5. Mac Safari 上方選單點「Develop > iPhone 裝置名稱 > 目前頁面」。
6. 開啟 Network，搜尋 `exchange-token`。

### 要看哪幾個訊號

請依照下面順序判讀：

1. `POST /auth/exchange-token` 有沒有真的發出。
2. 這個請求的 Response Status 是不是 `200`。
3. Response Headers 裡有沒有 `Set-Cookie`。
4. 接下來的 `GET /auth/me` 有沒有帶 `Cookie` request header。
5. `GET /auth/me` 的結果是不是 `200`，還是 `401`。

### 判讀對照表

| 觀察結果                                                             | 代表意義                                 | 下一步                                                 |
| -------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------ |
| 沒有 `POST /auth/exchange-token`                                     | 前端沒有成功進入 token exchange 流程     | 先看 LandingPage 是否拿到 `token`，再檢查 redirect URL |
| `POST /auth/exchange-token` 回 `4xx`                                 | token 無效、過期，或 request 本身有錯    | 檢查 token TTL、token 值、後端驗證邏輯                 |
| `POST /auth/exchange-token` 回 `200`，但後續 `GET /auth/me` 是 `401` | 最常見是 session cookie 沒被保存         | 優先懷疑跨站 cookie 被手機瀏覽器擋下                   |
| `POST /auth/exchange-token` 被 CORS 擋下                             | 前端 origin 不在 allow list 或預檢失敗   | 檢查 `CORS_ALLOW_ORIGINS` 與實際前端 origin            |
| `POST /auth/exchange-token` 根本打到錯站                             | 前端 bundle 用了錯的 `VITE_API_BASE_URL` | 回頭檢查 Vercel Environment Variables                  |

### 若沒有 Mac 可怎麼辦

若目前無法使用 Safari Web Inspector，可先採以下替代方式：

1. 確認 Vercel 的 `VITE_API_BASE_URL` 是否為 backend 正式 URL。
2. 確認 Lightsail runtime 的 `FRONTEND_URL`、`LINE_CALLBACK_URL`、`CORS_ALLOW_ORIGINS` 是否為正式值。
3. 在後端加入最小化 auth debug log，只記錄登入流程關鍵節點，不先改登入邏輯。

## 後端 Debug Log 建議

若無法直接看手機端 Network，最實用的替代方案是在後端加上最小化 debug log，確認請求有沒有進來，以及走到哪一步失敗。

### 目前已實作的第一輪 Debug Log

目前 backend 已先落第一輪 auth debug log，範圍如下：

1. `GET /auth/line/login`
2. `GET /auth/line/callback`
3. `POST /auth/exchange-token`
4. `GET /auth/me`
5. `POST /auth/logout`
6. OAuth state 驗證
7. LINE token exchange
8. LINE profile fetch
9. auth token 建立與驗證
10. LINE user upsert

目前 log 形式為單行 JSON，會附帶 request context，目的是讓 Lightsail container log 至少可以靠欄位搜尋與串接流程。

### 目前會看到的關鍵欄位

第一輪固定欄位包含：

1. `event`
2. `request_id`
3. `path`
4. `method`
5. `client_ip`
6. `user_agent`
7. `origin`
8. `referer`
9. `outcome`
10. `reason`
11. `status_code`
12. `user_id`

第二層 cookie / session debug 另外補了以下欄位：

1. `cookie_header_present`
2. `session_cookie_present`
3. `session_contains_user_id`
4. `session_cookie_name`
5. `same_site_policy`
6. `https_only`
7. `is_production`
8. `response_will_set_cookie`
9. `session_key_count`
10. `allow_credentials`

### 目前已實作的關鍵事件

第一輪至少可觀察以下事件：

1. `line_login_started`
2. `line_callback_received`
3. `line_callback_denied`
4. `oauth_state_validated`
5. `oauth_state_invalid`
6. `line_token_exchange_succeeded`
7. `line_token_exchange_failed`
8. `line_profile_fetch_succeeded`
9. `line_profile_fetch_failed`
10. `auth_token_created`
11. `auth_token_verified`
12. `auth_token_invalid`
13. `auth_token_expired`
14. `session_established`
15. `session_cookie_write_attempted`
16. `auth_me_succeeded`
17. `auth_me_cookie_missing`
18. `auth_me_cookie_present_but_session_missing`
19. `auth_me_user_missing`
20. `logout_completed`

### 如何用這批 log 判讀

部署後，若要判讀手機登入失敗落點，優先看同一輪請求附近是否出現以下組合：

1. 有 `line_callback_received`，但沒有 `session_established`。
   代表問題多半還在 callback 內部，例如 state、LINE token exchange 或 profile fetch。
2. 有 `session_cookie_write_attempted`，但接著又出現 `auth_me_cookie_missing`。
   代表後端已準備寫 session cookie，但後續 `/auth/me` 請求沒有帶回 cookie，優先懷疑跨站 cookie 問題。
3. 有 `auth_me_cookie_present_but_session_missing`。
   代表 request 已帶 Cookie header，且看起來帶了 session cookie，但 server 端 session 仍沒有 `user_id`，這時要回頭查 cookie 名稱、session 解析或簽名問題。
4. 有 `auth_token_invalid` 或 `auth_token_expired`。
   代表問題落在 token handoff 本身，而不是 `/auth/me`。
5. 有 `auth_me_user_missing`。
   代表 session 裡有 user id，但 DB 查不到使用者，這是另一類問題。

### 建議記錄哪些事件

最少記以下事件即可：

1. `GET /auth/line/login` 被呼叫，並記錄 request path 與 user agent。
2. `GET /auth/line/callback` 被呼叫，並記錄是否有 `code`、`state`、`error`。
3. callback 建立 auth token 後，記錄 user id 與 redirect target，但不要記完整 token。
4. `POST /auth/exchange-token` 被呼叫，記錄 request origin、referer、user agent。
5. exchange 成功後，記錄 user id 與「session 已建立」。
6. `GET /auth/me` 回 `401` 時，記錄是否帶 session cookie。

### 不建議直接記錄的資訊

以下資訊不要直接打進 log：

1. 完整 session cookie 值
2. 完整 auth token
3. LINE access token
4. 使用者敏感個資

### 在目前架構下要去哪裡看 log

以目前專案來說，若只是把 debug log 打到 stdout 或 stderr，實際上就是到 Lightsail Container Service 的 container log 看。

換句話說，目前答案是：

1. 是，最直接的查看位置通常還是 Lightsail。
2. 但不代表只能這樣做，也不代表這是最好的做法。

### 為什麼 Lightsail log 會難用

Lightsail log 不好用是正常現象，常見痛點包括：

1. 搜尋與篩選能力有限。
2. 不適合長時間追蹤單一使用者流程。
3. 對跨多請求的 auth flow 缺乏 request correlation。
4. 手機登入問題通常需要把 callback、exchange、me 三段事件串起來看，Lightsail 原生介面做這件事不順手。

### 可以改善的空間

若後續要改善，不一定要一次升級整個部署架構，可以分階段做：

1. 第一階段：把 auth debug log 改成結構化 JSON，至少帶 `event`, `path`, `user_agent`, `origin`, `referer`, `request_id`。
2. 第一階段：前端每次登入流程產生一個簡單 request id，前後端 log 都帶同一個 id，方便串整條流程。
3. 第二階段：把關鍵 auth 事件另外送到外部 log 平台，例如 Better Stack、Axiom、Datadog 或 Sentry breadcrumb。
4. 第二階段：若未來真的要長期做營運排查，可評估從 Lightsail 遷移到更適合觀測性的環境，例如 ECS Fargate + CloudWatch。

### 目前最務實的做法

對 MVP 階段來說，最務實的順序通常是：

1. 先補最小化 auth debug log。
2. log 格式用 JSON，不要只印自由文字。
3. 先只追 callback、exchange-token、auth/me 三個端點。
4. 等根因確認後，再決定是否要導入外部 log 平台。
