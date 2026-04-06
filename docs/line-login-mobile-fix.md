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

| 屬性 | 說明 |
|---|---|
| 無法偽造 | Token 以伺服器 `SESSION_SECRET_KEY` + `itsdangerous` 簽名 |
| 有效期限制 | 2 分鐘 TTL，超時後 `verify_auth_token` 拋 400 |
| 傳輸安全 | Token 在 HTTPS URL 中，受 TLS 保護 |
| 清除 URL | 前端 exchange 成功後立即以 `setSearchParams({}, { replace: true })` 清除，不留在瀏覽器歷史 |
| 無需 DB migration | 複用既有的 `TimestampSigner` 模式，不新增 table |

> **注意**：2 分鐘 TTL 代表在 LINE 導回瀏覽器後，使用者有 2 分鐘的時間完成 exchange。
> 若需要更嚴格的一次性 token（完全防 replay），可改為在 DB 記錄已使用的 token，
> 但對於目前的使用情境，2 分鐘 TTL 已足夠安全。

## 測試

`backend/tests/test_auth.py` 涵蓋以下情境：

| 測試 | 說明 |
|---|---|
| `test_auth_flow_creates_session_and_logout_clears_it` | 完整流程：callback redirect 含 token → exchange → /auth/me 200 → logout → 401 |
| `test_get_line_callback_updates_existing_user` | callback redirect 改為含 token 的 `/` |
| `test_exchange_token_success` | 有效 token → 200 + session 建立 |
| `test_exchange_token_expired` | 過期 token → 400 |
| `test_exchange_token_invalid` | 格式錯誤 token → 400 |
