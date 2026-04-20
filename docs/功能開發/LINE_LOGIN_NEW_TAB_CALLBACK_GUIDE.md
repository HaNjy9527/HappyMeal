# LINE Login 導回新頁未顯示登入狀態的處理指南

建立時間：2026-04-13 23:09

## 快速導覽

- 文件類型：解說（Explanation）
- 目標讀者：使用 Python 開發後端，且前端有 SPA 或站內導頁需求的工程師
- 使用者目標：理解 LINE Login 在導回時另開新頁或切換頁面上下文時，為什麼常出現「其實已登入，但畫面看起來沒登入」，以及如何設計一套更穩定的流程
- 範圍包含：
  - 本專案目前有效的處理思路
  - 本專案現況中的主要缺點與風險
  - 可套用到其他 Python 後端專案的推薦流程
  - FastAPI 實作建議與前後端責任分工
- 範圍不包含：
  - LINE Developers Console 逐步申請教學
  - 完整會員系統資料表設計
  - 特定前端框架元件實作細節

## 1. 問題定義

LINE Login 在實務上常出現一個看似矛盾的症狀：

1. 使用者已經在 LINE 授權成功。
2. 後端也已經成功換到 access token，甚至完成會員登入。
3. 但回到網站時，頁面卻仍顯示「未登入」。

這個問題通常不是單一 bug，而是「登入成功」與「前端畫面知道已登入」之間的資訊傳遞斷掉。

最常見的成因有四類：

1. LINE 導回時開了新的頁面上下文，原本頁面中的記憶體狀態不存在。
2. 登入資訊只存在某個頁面的暫存 state，沒有落到可跨頁面讀取的持久狀態。
3. callback 頁面雖然收到登入結果，但沒有再主動同步前端的會員狀態。
4. 原本想回去的頁面路徑遺失，導致登入成功後回到錯的頁面或首頁。

## 2. 本專案的核心經驗

本專案目前真正有效的部分，不是「把 LINE 新開的頁面關掉」，而是「即使回來時不是原本的頁面上下文，也能知道接下來要去哪裡，並重新建立登入狀態」。

也就是說，它解的是：

1. 登入後應該回哪個站內頁面。
2. callback 頁面如何拿到登入結果。
3. callback 頁面如何把登入結果轉成前端可用的已登入狀態。

它沒有解的是：

1. 操作瀏覽器 popup 或新開視窗本身。
2. 主動關閉 LINE 導回的新頁。
3. 與原始開啟頁面做 `window.opener` 或 `postMessage` 溝通。

## 3. 本專案目前的實際流程

以下是本專案現況的實際登入鏈路，省略 UI 細節，只保留關鍵資訊傳遞。

### 3.1 登入前

1. 前端使用者點擊 LINE 登入。
2. 前端把目前站內位置記成 `returnUrl`。
3. 前端同時：
   - 先把 `returnUrl` 存到 browser storage。
   - 呼叫後端 `/api/auth/line/login?returnUrl=...`。

### 3.2 產生授權網址

1. 後端產生 LINE 授權 URL。
2. 後端把 `returnUrl` 包進 OAuth `state`。
3. 前端把瀏覽器導向 LINE 授權頁。

### 3.3 LINE 授權完成

1. LINE 導回後端 callback API。
2. 後端用 `code` 交換 LINE token。
3. 後端取得 LINE profile。
4. 後端查詢或建立本站會員。
5. 後端建立本站登入憑證。

### 3.4 回到前端 callback 頁

1. 後端從 `state` 取回 `returnUrl`。
2. 後端再把瀏覽器導到前端 callback 頁。
3. 前端 callback 頁完成登入狀態初始化。
4. 前端導回原本的站內路徑。

這個思路的價值在於：

即使 LINE 回來時已經不是原本的分頁或原本的 React state，上述流程仍能靠 callback 頁重新建立前端狀態。

## 4. 本專案值得保留的做法

以下做法是值得延續到其他專案的。

### 4.1 保留登入前的站內目的地

登入前先記住使用者原本的站內位置，是必要設計，不是附加功能。

如果沒有這一步，即使登入成功，也常只會回首頁，讓使用者覺得登入流程被中斷。

實作要點：

1. 只允許站內路徑，例如 `/member/orders?tab=pending`。
2. 不要接受完整外部 URL。
3. 可以同時在前端暫存與後端 state 中各存一份，但後端 state 應是主要可信來源。

### 4.2 使用專用 callback 頁負責狀態初始化

callback 頁不要只是顯示「登入成功」，它真正的責任應是：

1. 讀取後端導回的結果。
2. 初始化前端登入狀態。
3. 重新拉取目前會員資料。
4. 導回原本頁面。

這樣就算 LINE 導回的是新頁，上下文也能重新建立。

### 4.3 讓登入成功與會員資料同步分成兩步

推薦把「登入成功」與「畫面知道誰已登入」拆開：

1. 後端先建立本站 session 或 token。
2. 前端 callback 頁再呼叫 `/api/auth/me` 或 `/api/member/me` 把當前會員資料抓回來。

這樣可以避免前端只靠 query string 或一段臨時資料推論登入狀態。

## 5. 本專案不建議沿用的部分

以下是本專案現況中的負面經驗，建議在下一個專案直接避開。

### 5.1 不要把 access token 放在 query string

本專案目前把登入 token 透過 `?t=...` 帶回前端 callback。這種做法雖然快，但風險高：

1. 可能進入瀏覽器歷史紀錄。
2. 可能被 proxy、log、監控工具記錄。
3. 若有第三方跳轉或資源請求，可能透過 referrer 洩漏。

建議改法：

1. 後端 callback 完成後直接設定 httpOnly cookie。
2. 然後只帶一個非敏感的結果參數，例如 `?login=success`。
3. 前端 callback 頁再用 cookie 身分去呼叫 `/api/auth/me`。

### 5.2 不要讓 state 只剩下導頁用途

OAuth `state` 的本質是防止 CSRF，不只是拿來塞 `returnUrl`。

如果 `state` 沒有被驗證，就等於把安全保護拆掉，只剩下一個搬運資料的容器。

建議改法：

1. `state` 應包含 nonce 或 request id。
2. 後端 callback 時必須驗證這個 `state` 是自己先前發出去的。
3. 驗證通過後才能交換 token 與建立登入狀態。

### 5.3 不要只靠 localStorage 判斷是否已登入

若前端是否登入完全仰賴 localStorage token，會有兩種問題：

1. 安全性較弱，XSS 風險高。
2. 新頁、刷新、或多分頁同步時容易出現畫面狀態不一致。

建議改法：

1. 用 httpOnly secure cookie 保存 session 或 access token。
2. 前端載入時一律透過 `/api/auth/me` 取得目前會員。
3. 前端 memory state 只是快取，不是登入真相來源。

### 5.4 不要讓新舊 callback 流程並存太久

當系統同時保留舊 callback 頁、舊 API、舊文件時，很快就會出現：

1. 文件寫的是舊流程。
2. 程式跑的是新流程。
3. 新人維護時看不出哪一套才是正式入口。

建議改法：

1. 明確只保留一個前端 callback 路由。
2. 明確只保留一個後端 auth callback API。
3. 一旦新流程上線，立刻清理舊文件與舊碼。

## 6. 推薦給下一個 Python 專案的設計

以下是一套更穩定、也更適合 Python/FastAPI 後端的推薦流程。

### 6.1 設計目標

這套流程要同時滿足四件事：

1. 即使 LINE 導回的是新頁，也能顯示已登入。
2. 登入後能回到原本想去的站內頁面。
3. 不把敏感 token 放在 URL。
4. 保留 OAuth `state` 的安全用途。

### 6.2 推薦流程

#### 步驟 1：前端發起登入

前端呼叫：

```text
GET /api/auth/line/login?next=/member/orders
```

規則：

1. `next` 只能是站內路徑。
2. 前端可先把 `next` 存在 sessionStorage 作為備援。
3. 後端仍要把 `next` 一起編進可驗證的 `state`。

#### 步驟 2：後端建立可驗證 state

後端應至少產生：

1. `request_id`
2. `nonce`
3. `next`
4. `expires_at`

然後用兩種方式擇一：

1. 存到 Redis / DB / server-side session，回傳隨機 `state` key。
2. 把內容做簽名後編成不可竄改的 `state`。

#### 步驟 3：LINE callback 回到後端

後端收到 `code` 與 `state` 後：

1. 驗證 `state` 是否存在、未過期、未使用。
2. 驗證通過後再交換 LINE token。
3. 取得 LINE profile。
4. 查詢或建立本站會員。
5. 建立本站 session。
6. 將 session 寫入 httpOnly cookie。

#### 步驟 4：後端 redirect 到前端 callback 頁

後端 redirect 到：

```text
/auth/callback?login=success&next=/member/orders
```

注意：

1. 這裡不要帶 access token。
2. `next` 仍要做站內路徑白名單檢查。

#### 步驟 5：前端 callback 頁重新取得目前會員

前端 callback 頁開啟後：

1. 讀取 `next`。
2. 呼叫 `/api/auth/me`。
3. 若成功取得會員資料，將前端 auth store 設為已登入。
4. 然後導到 `next`。

這一步是解決「新頁明明成功登入，但畫面還沒同步」的關鍵。

## 7. 為什麼這套設計能解掉新頁未登入

關鍵在於：

前端不再依賴「原本那個頁面裡的記憶體狀態」，而是依賴「後端已建立好的 session」。

只要瀏覽器被導回本站 callback 頁，不論是不是新頁，只要 cookie 已存在：

1. callback 頁就能讀到登入後的後端身分。
2. callback 頁就能重新抓 `/api/auth/me`。
3. callback 頁就能把畫面狀態重建成已登入。

這個模型比依賴 `window.opener`、popup、或 query token 都穩定。

## 8. FastAPI 後端建議實作

以下為推薦的後端責任分工，不綁定特定 ORM。

### 8.1 路由職責

建議保留三個主要 API：

1. `GET /api/auth/line/login`
2. `GET /api/auth/line/callback`
3. `GET /api/auth/me`

### 8.2 login API 應做的事

```python
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/auth/line/login")
def line_login(next: str = "/") -> dict:
    safe_next = normalize_next_path(next)
    state = create_login_state(next_path=safe_next)
    auth_url = build_line_authorization_url(state=state)
    return {"auth_url": auth_url}
```

重點：

1. `normalize_next_path` 必須拒絕外站 URL。
2. `create_login_state` 必須可驗證，不是純字串拼接。

### 8.3 callback API 應做的事

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/api/auth/line/callback")
async def line_callback(code: str, state: str) -> RedirectResponse:
    login_context = validate_login_state(state)
    if not login_context.is_valid:
        raise HTTPException(status_code=400, detail="Invalid login state")

    line_tokens = await exchange_line_code(code=code)
    profile = await fetch_line_profile(access_token=line_tokens.access_token)
    member = await get_or_create_member_from_line(profile=profile)

    response = RedirectResponse(
        url=f"/auth/callback?login=success&next={login_context.next_path}"
    )
    issue_login_session_cookie(response=response, member=member)
    mark_login_state_as_used(state)
    return response
```

重點：

1. callback 成功時，先寫 cookie，再 redirect。
2. `state` 驗證失敗時應立即拒絕。
3. `state` 使用後應失效，避免重放。

### 8.4 me API 應做的事

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


@router.get("/api/auth/me")
async def auth_me(current_member = Depends(get_current_member)) -> dict:
    return {
        "member_id": current_member.id,
        "display_name": current_member.display_name,
        "line_user_id": current_member.line_user_id,
    }
```

前端 callback 頁只要打這支 API，就知道畫面該不該顯示為已登入。

## 9. 前端配合重點

雖然本文聚焦 Python 後端，但要真正解決畫面顯示問題，前端至少要做到以下三件事：

1. 登入按鈕送出 `next` 或 `returnUrl`。
2. callback 頁在載入時主動呼叫 `/api/auth/me`。
3. callback 頁完成會員資訊同步後再導頁。

如果前端有多分頁同步需求，可以再加：

1. `BroadcastChannel`
2. `storage` event

但這是額外優化，不是核心解法。

核心解法仍然是：

「登入真相在後端 session，前端 callback 頁負責重新拉取並重建畫面狀態。」

## 10. 實作檢查清單

導入到下一個專案時，可用以下清單自我檢查。

### 必要項目

- 有保存登入前的站內 `next` 路徑
- `next` 只允許站內相對路徑
- OAuth `state` 可驗證且有時效
- callback 時有驗證 `state`
- callback 成功後由後端先建立 session
- session 透過 httpOnly cookie 傳遞
- callback redirect URL 不帶 access token
- 前端 callback 頁會呼叫 `/api/auth/me`
- 前端 callback 頁會在同步會員資料後再導頁

### 不建議項目

- 把 access token 放在 query string
- 只用 localStorage 判斷是否登入
- 只在原始頁面 memory state 裡保存登入結果
- callback 成功後不重新抓目前會員資料
- 新舊 callback 流程並存且沒有退場計畫

## 11. 給本專案與下一個專案的結論

本專案值得保留的核心經驗是：

1. 登入前的目標頁要保留下來。
2. callback 頁要負責重新建立前端登入狀態。
3. 不要把「原本頁面還在不在」當成登入成功的前提。

本專案不建議延續到下一個專案的部分是：

1. token 放在 URL。
2. state 沒有被完整驗證。
3. 前端過度依賴 localStorage token。
4. 新舊流程並存太久。

如果下一個專案同樣使用 Python 開發後端，最穩定的做法是：

1. 後端 callback 驗證 state。
2. 後端建立 session cookie。
3. 前端 callback 頁以 `/api/auth/me` 重建登入畫面。
4. 最後再導回原本頁面。

這樣就算 LINE 導回時是新頁，也能正確顯示已登入。

## 12. 本專案對照檔案

若要回頭核對本專案現況，可參考以下檔案：

1. `frontend/src/components/auth/LineLoginButton.tsx`
2. `frontend/src/contexts/AuthContext.tsx`
3. `frontend/src/pages/AuthCallback.tsx`
4. `backend/app/api/auth/routes.py`
5. `backend/app/services/auth_service.py`
6. `backend/app/integrations/line/login.py`
