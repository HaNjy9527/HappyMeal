# HappyMeal LINE Login 實作指南 v1

- 文件名稱：LINE Login 實作指南
- 版本：v2
- 日期：2026-04-03
- 狀態：Draft
- 用途：定義 LINE Login OAuth 2.0 完整實作流程、驗收標準與常見卡關，聚焦單一功能完整做完
- 決策紀錄：本文件採用「直接用正式環境測試」策略，不使用 ngrok 進行本地開發測試

---

## 1. 文件定位

本文件只處理 LINE Login OAuth 的前後端完整實作。

本文件不處理以下內容：

1. Profile 建檔流程
2. Consent 同意流程
3. 分析主流程
4. 任何與 LINE Login 無關的頁面或 API

LINE Login 完成後的驗收條件是：使用者可在瀏覽器完成 LINE 授權並取得登入狀態，後端可識別身份，前端可顯示登入使用者資訊。

---

## 2. 先理解 LINE Login 在做什麼

### 2.1 OAuth 2.0 授權碼流程

LINE Login 使用標準 OAuth 2.0 Authorization Code Flow，流程如下：

```
使用者點擊「LINE 登入」
        │
        ▼
前端導向 LINE 授權頁（帶 client_id、redirect_uri、state）
        │
使用者在 LINE 頁面同意授權
        │
        ▼
LINE 將使用者重導回 redirect_uri（帶 code、state）
        │
        ▼
後端用 code 向 LINE 換取 access_token
        │
        ▼
後端用 access_token 向 LINE 取得使用者資料
        │
        ▼
後端建立或更新 User 資料，建立 session
        │
        ▼
前端取得登入狀態，顯示使用者資訊
```

### 2.2 關鍵安全概念

**state 參數**：由後端或前端生成的隨機字串，用於防止 CSRF 攻擊。發送授權請求時帶入，callback 時驗證是否一致。

**redirect_uri**：必須在 LINE Developers Console 事先登錄，完全比對，多一個斜線也不行。

**code 只能用一次**：授權碼換 token 後即失效，不可重複使用。

**access_token 不要存在前端**：token 只在後端使用，前端只持有 session cookie 或 JWT。

---

## 3. 前置設定：LINE Developers Console

### 3.1 建立 LINE Login Channel

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立或選擇 Provider
3. 點「Create a new channel」→ 選「LINE Login」
4. 填寫：
   - Channel name：`HappyMeal`
   - Channel description：任意
   - App types：勾選「Web app」
5. 同意 Terms 並建立

### 3.2 取得憑證

建立完成後，進入 channel 設定頁面，記錄以下兩個值：

| 項目           | 位置                            | 加入到                          |
| -------------- | ------------------------------- | ------------------------------- |
| Channel ID     | Basic settings → Channel ID     | `.env` 的 `LINE_CHANNEL_ID`     |
| Channel Secret | Basic settings → Channel secret | `.env` 的 `LINE_CHANNEL_SECRET` |

### 3.3 設定 Callback URL

LINE Login → Callback URL 欄位填入正式環境的 redirect_uri：

```
https://happymeal-backend.xxxxxxxx.ap-northeast-1.cs.amazonlightsail.com/auth/line/callback
```

> 這個地址在 Lightsail Container Service 建立完成後就固定了，不會再變。

> 重要：URL 需完全一致，不能有多餘的斜線或參數。`xxxxxxxx` 替換成你的 Lightsail 實際產生的 ID。

### 3.4 設定 Scopes

在 LINE Login → Scopes，勾選需要的資料範圍：

- `profile`（必要）：取得 display name 與頭像
- `openid`（建議）：取得穩定的 user ID
- `email`（選用）：PRD FR-01 說明若 LINE 未提供 email 不可阻塞登入，所以不強制

---

## 4. 測試策略說明

### 4.1 為什麼直接用正式環境測試

LINE Login 的 callback 要求必須是 HTTPS，且必須是 LINE 伺服器能打到的公開地址。本地的 `localhost` 不符合這兩個條件，傳統做法是用 ngrok 建立臨時 tunnel。

HappyMeal 採用不同策略：**直接在正式環境（Lightsail）上測試 LINE Login**。

原因：

1. Lightsail 本身已有 HTTPS 和固定公開 URL，天然符合 LINE 的要求
2. CI/CD pipeline 已跑通，push 到 main 就自動部署，迭代速度足夠
3. MVP 階段沒有真實使用者，正式環境出問題影響只有開發者自己
4. 省去每次啟動 ngrok、更新 URL、重啟 container 的重複作業

### 4.2 開發流程

```
在本機寫程式碼
      │
      ▼
push 到 main branch
      │
      ▼
GitHub Actions 自動部署到 Lightsail
      │
      ▼
打開正式環境 URL 測試 LINE Login 流程
      │
      ▼
有問題就改程式碼，再 push
```

> 如果未來需要在本地 debug 複雜問題，再安裝 ngrok 即可，Lightsail Callback URL 設定頁面支援填入多個 URL。

---

## 5. 後端實作

### 5.1 新增環境變數

`.env` 新增（本機開發用，不 commit）：

```env
LINE_CHANNEL_ID=your_channel_id
LINE_CHANNEL_SECRET=your_channel_secret

# Session 設定
SESSION_SECRET_KEY=your_random_secret_key_at_least_32_chars
```

**GitHub Secrets 新增**（CI/CD 部署時注入，這才是正式環境實際讀取的值）：

| Secret 名稱           | 值                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------- |
| `LINE_CHANNEL_ID`     | LINE Console 的 Channel ID                                                                    |
| `LINE_CHANNEL_SECRET` | LINE Console 的 Channel Secret                                                                |
| `LINE_CALLBACK_URL`   | `https://happymeal-backend.xxxxxxxx.ap-northeast-1.cs.amazonlightsail.com/auth/line/callback` |
| `SESSION_SECRET_KEY`  | 自行生成的隨機字串（至少 32 字元）                                                            |
| `FRONTEND_URL`        | Vercel 部署後的前端 URL                                                                       |

`pydantic-settings` Settings class 新增對應欄位：

```python
# app/config.py（或現有 settings 位置）

class Settings(BaseSettings):
    # ... 現有欄位 ...
    line_channel_id: str
    line_channel_secret: str
    line_callback_url: str
    session_secret_key: str
```

### 5.2 安裝依賴

```bash
# 在 backend 目錄，加入以下套件
pip install httpx itsdangerous python-multipart
```

更新 `requirements.txt`：

```
httpx          # 呼叫 LINE API 的 HTTP client
itsdangerous   # session 簽名
```

> `python-multipart` 通常 FastAPI 已內建，確認 requirements.txt 有就好。

### 5.3 實作 Auth Router

```python
# app/routers/auth.py

import secrets
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models import User
from app.session import create_session, get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

LINE_AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"


# ── GET /auth/line/login ─────────────────────────────────────────────────────

@router.get("/line/login")
def line_login(request: Request):
    """
    生成 state，重導向 LINE 授權頁。
    state 存入 session，用於 callback 時驗證。
    """
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    params = {
        "response_type": "code",
        "client_id": settings.line_channel_id,
        "redirect_uri": settings.line_callback_url,
        "state": state,
        "scope": "profile openid",
    }

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{LINE_AUTH_URL}?{query_string}")


# ── GET /auth/line/callback ──────────────────────────────────────────────────

@router.get("/line/callback")
def line_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db),
):
    """
    接收 LINE callback，驗證 state，換 token，取 profile，建立或更新 User。
    """
    # 使用者拒絕授權
    if error:
        return RedirectResponse(url="/?error=line_auth_denied")

    # 驗證 state（防 CSRF）
    session_state = request.session.pop("oauth_state", None)
    if not state or state != session_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # 用 code 換 access_token
    token_response = httpx.post(
        LINE_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.line_callback_url,
            "client_id": settings.line_channel_id,
            "client_secret": settings.line_channel_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange token")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    # 用 access_token 取 profile
    profile_response = httpx.get(
        LINE_PROFILE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if profile_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get LINE profile")

    profile = profile_response.json()
    line_user_id = profile.get("userId")
    display_name = profile.get("displayName", "")
    avatar_url = profile.get("pictureUrl", "")

    # 建立或更新 User
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    if not user:
        user = User(
            line_user_id=line_user_id,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        db.add(user)
    else:
        user.display_name = display_name
        user.avatar_url = avatar_url

    db.commit()
    db.refresh(user)

    # 建立 session
    request.session["user_id"] = str(user.id)

    # 登入後重導向前端
    frontend_url = settings.frontend_url  # 例如 http://localhost:5173
    return RedirectResponse(url=f"{frontend_url}/home")


# ── GET /auth/me ─────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    """
    回傳目前登入使用者資訊。未登入回傳 401。
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "theme_preference": user.theme_preference,
    }


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}
```

### 5.4 設定 Session Middleware

FastAPI 本身不內建 session，需要用 `itsdangerous` 加 middleware。

```python
# main.py

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth
from app.config import get_settings

settings = get_settings()

app = FastAPI()

# Session middleware 要加在最上面
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="happymeal_session",
    max_age=60 * 60 * 24 * 7,  # 7 天
    https_only=True,             # 正式環境 Lightsail 有 HTTPS，設 True
    same_site="lax",
)

app.include_router(auth.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

> **注意**：`SessionMiddleware` 必須在 CORS middleware 之前或注意順序，否則 cookie 可能無法正確回傳。

### 5.5 Settings 新增 frontend_url

```python
# app/config.py

class Settings(BaseSettings):
    # ... 其他欄位 ...
    frontend_url: str  # 正式環境由 GitHub Secrets 注入，無預設值
```

GitHub Secrets 新增 `FRONTEND_URL`，值為 Vercel 部署後的前端 URL，例如：

```
FRONTEND_URL=https://happymeal.vercel.app
```

---

## 6. 前端實作

### 6.1 登入按鈕

最簡單的方式：直接用 `<a>` 或 `window.location.href` 導向後端的 login endpoint，讓後端處理整個 OAuth redirect。

```tsx
// src/components/LineLoginButton.tsx

const BACKEND_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function LineLoginButton() {
  const handleLogin = () => {
    window.location.href = `${BACKEND_URL}/auth/line/login`;
  };

  return <button onClick={handleLogin}>使用 LINE 登入</button>;
}
```

### 6.2 取得登入狀態

```tsx
// src/hooks/useAuth.ts

import { useQuery } from "@tanstack/react-query";

const BACKEND_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function fetchMe() {
  const res = await fetch(`${BACKEND_URL}/auth/me`, {
    credentials: "include", // 帶 cookie
  });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error("Failed to fetch user");
  return res.json();
}

export function useAuth() {
  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 分鐘
  });

  return { user, isLoading, isLoggedIn: !!user };
}
```

### 6.3 Route Guard（保護需要登入的頁面）

```tsx
// src/components/RequireAuth.tsx

import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>載入中...</div>;
  if (!user) return <Navigate to="/" replace />;

  return <>{children}</>;
}
```

Router 使用：

```tsx
// src/App.tsx

import { RequireAuth } from "./components/RequireAuth";

<Route
  path="/home"
  element={
    <RequireAuth>
      <HomePage />
    </RequireAuth>
  }
/>;
```

### 6.4 登出

```tsx
// src/hooks/useLogout.ts

import { useMutation, useQueryClient } from "@tanstack/react-query";

const BACKEND_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await fetch(`${BACKEND_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    },
    onSuccess: () => {
      queryClient.setQueryData(["me"], null);
      window.location.href = "/";
    },
  });
}
```

### 6.5 前端環境變數

Vercel 部署設定（Project Settings → Environment Variables）：

```env
VITE_API_BASE_URL=https://happymeal-backend.xxxxxxxx.ap-northeast-1.cs.amazonlightsail.com
```

本地開發若要跑前端（非 LINE Login 相關功能），`.env.local`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 7. CORS 設定確認

LINE Login callback 由瀏覽器執行 redirect，不是 CORS 請求。但前端呼叫 `/auth/me` 和 `/auth/logout` 需要 CORS + cookie 正確設定。

確認 `main.py` 的 CORS middleware 包含以下設定：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-vercel-app.vercel.app",
    ],
    allow_credentials=True,   # 必要：允許帶 cookie
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> `allow_credentials=True` 且 `allow_origins` 不能是 `["*"]`，必須明確列出 origin。

---

## 8. 正式環境測試流程

每次要驗證 LINE Login 的標準流程：

```
1. 確認 GitHub Secrets 都已設定（LINE_CHANNEL_ID、LINE_CHANNEL_SECRET、
   LINE_CALLBACK_URL、SESSION_SECRET_KEY、FRONTEND_URL）
2. push 到 main，等 GitHub Actions 部署完成
3. 確認 Lightsail Container Service 狀態為 Running
4. 打開 Vercel 前端 URL
5. 點擊 LINE 登入按鈕
6. 完成 LINE 授權
7. 確認重導回前端 /home
8. 確認頁面顯示登入使用者的 display name
9. 打開瀏覽器 DevTools → Network，確認 /auth/me 回傳正確資料
10. 點擊登出，確認回到未登入狀態
```

---

## 9. 驗收條件

### 9.1 後端驗收

| 項目                  | 驗收方式                        | 完成條件                                   |
| --------------------- | ------------------------------- | ------------------------------------------ |
| `/auth/line/login`    | 瀏覽器直接打開                  | 成功 redirect 到 LINE 授權頁               |
| state 防 CSRF         | 手動篡改 callback 的 state 參數 | 後端回傳 400                               |
| `/auth/line/callback` | 完整走一次 LINE 授權            | User 成功建立或更新於 DB                   |
| session 建立          | 看 response headers             | 有 `Set-Cookie: happymeal_session`         |
| `/auth/me` 登入狀態   | 登入後呼叫                      | 回傳 `id`、`display_name`、`avatar_url`    |
| `/auth/me` 未登入     | 無 cookie 呼叫                  | 回傳 401                                   |
| `/auth/logout`        | 登入後 POST                     | 清除 session，後續 `/auth/me` 回 401       |
| 首次登入建立 User     | 全新 LINE 帳號登入              | DB 新增一筆 User                           |
| 重複登入更新 User     | 同帳號第二次登入                | DB 更新 display_name 與 avatar_url，不新增 |

### 9.2 前端驗收

| 項目                 | 驗收方式         | 完成條件                               |
| -------------------- | ---------------- | -------------------------------------- |
| Landing 頁有登入按鈕 | 瀏覽器查看       | 按鈕存在且可點擊                       |
| 點擊登入按鈕         | 手動操作         | 成功跳轉 LINE 授權頁                   |
| 授權後重導回前端     | 完整走一次       | 停在 `/home` 而非 404                  |
| 顯示使用者資訊       | 登入後查看 Home  | 顯示 LINE display name 或頭像          |
| 未登入時保護頁面     | 直接打開 `/home` | 重導回 Landing 頁                      |
| 登出後狀態清除       | 點擊登出         | 回到未登入狀態，再打 `/auth/me` 得 401 |

### 9.3 安全驗收

| 項目              | 驗收方式                                | 完成條件                            |
| ----------------- | --------------------------------------- | ----------------------------------- |
| 前端無 LINE token | 檢查 localStorage / sessionStorage      | 找不到任何 LINE access_token        |
| Cookie 設定       | 瀏覽器 DevTools → Application → Cookies | `happymeal_session` 存在且 HttpOnly |
| `.env` 不進 repo  | git status                              | 沒有 `.env` 在 staged 或 committed  |

---

## 10. 已知範圍邊界

本文件完成後，LINE Login 視為可用。以下功能不在本文件範圍：

| 功能             | 說明                                           |
| ---------------- | ---------------------------------------------- |
| Profile 建檔     | 登入後若無 UserProfile，另行處理               |
| Consent 流程     | 首次使用敏感功能前的同意，另行處理             |
| 首頁 Dashboard   | 登入後的完整 Home 頁面，另行處理               |
| JWT 替換 session | MVP 使用 server-side session，如需無狀態再遷移 |
| 多登入方式       | PRD 8.2 明確排除，不在第一版                   |

---

## 11. 常見卡關

| 問題                          | 原因                                                                         | 解法                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `Invalid redirect_uri`        | LINE Console 的 Callback URL 和 GitHub Secrets 的 `LINE_CALLBACK_URL` 不一致 | 確認兩者完全相同，特別注意結尾有無斜線                                      |
| Cookie 沒帶到前端             | fetch 沒有 `credentials: "include"`                                          | 所有需要 session 的請求加 `credentials: "include"`                          |
| CORS 錯誤                     | `allow_origins` 設成 `"*"` 但又有 `allow_credentials=True`                   | `allow_origins` 必須明確列出 Vercel 的 origin，不能是 `"*"`                 |
| `/auth/me` 一直回 401         | Session cookie 因為 domain 不同無法跨域帶回                                  | 確認 CORS `allow_credentials=True` 且前端 fetch 有 `credentials: "include"` |
| state mismatch                | SessionMiddleware 順序問題                                                   | 確認 `SessionMiddleware` 的 `add_middleware` 在 `CORSMiddleware` 之前       |
| 登入後重導到後端 URL 而非前端 | `FRONTEND_URL` 這個 GitHub Secret 未設定或設錯                               | 確認 GitHub Secrets 的 `FRONTEND_URL` 指向 Vercel 前端 URL                  |
| Container 部署後一直 restart  | 新加的環境變數在 GitHub Secrets 沒有設定，Settings 初始化失敗                | 確認所有 Settings 欄位都有對應的 Secret                                     |

---

## 12. 對應文件

| 問題                     | 查哪裡                                                                                       |
| ------------------------ | -------------------------------------------------------------------------------------------- |
| LINE Login OAuth 規格    | [LINE Developers 文件](https://developers.line.biz/en/docs/line-login/integrate-line-login/) |
| HappyMeal Auth API 設計  | `Architecture_v1` Section 9.1                                                                |
| Session 安全考量         | `Architecture_v1` Section 11                                                                 |
| 部署後 Callback URL 更新 | `HappyMeal_AWS_Step4_Lightsail_部署指引-v1.md` 常見卡關                                      |
| 整體開發順序             | `HappyMeal_Dev_Kickoff.md`                                                                   |
