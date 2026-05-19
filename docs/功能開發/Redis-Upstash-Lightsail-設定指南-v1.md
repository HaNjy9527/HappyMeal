# Upstash Redis 設定指南（AWS Lightsail 環境）

建立時間：2026-05-19 09:00

---

## 快速導覽

- [一、前置條件](#一前置條件)
- [二、Upstash 申請與登入](#二upstash-申請與登入)
- [三、建立 Redis 資料庫](#三建立-redis-資料庫)
- [四、取得連線字串](#四取得連線字串)
- [五、Lightsail 環境變數設定](#五lightsail-環境變數設定)
- [六、本機開發環境設定](#六本機開發環境設定)
- [七、驗證連線是否正常](#七驗證連線是否正常)
- [八、費用說明與升級時機](#八費用說明與升級時機)

---

## 一、前置條件

在開始之前，請確認以下事項已就緒：

- **後端已部署在 AWS Lightsail**（Instance 或 Container Service 皆適用）
- **已有 GitHub 帳號**（Upstash 支援 GitHub OAuth 快速登入，無需另外填寫信用卡）
- **本機已有 Docker 和 Docker Compose**（用於本機開發環境驗證）
- **程式碼已完成 Redis Cache 實作**（參考：[Redis-RAG-Cache-設計說明-v1.md](./Redis-RAG-Cache-設計說明-v1.md)）

---

## 二、Upstash 申請與登入

1. 前往 [https://console.upstash.com](https://console.upstash.com)
2. 點擊右上角 **「Sign Up」** 或 **「Log In」**
3. 選擇 **「Continue with GitHub」**，使用 GitHub 帳號授權登入
4. 登入後會進入 Upstash Console 首頁

> **為什麼選 Upstash？**
> Upstash 是 Serverless Redis，透過標準 Redis 協定連線，無需在 Lightsail 內部另開 instance、不需要 VPC peering、不需要管理 Redis 設定檔。
> AWS 自家的 ElastiCache 雖然功能完整，但需要與 Lightsail 做 VPC Peering（設定繁瑣），且費用對早期產品不划算。

---

## 三、建立 Redis 資料庫

1. 在 Upstash Console 點擊 **「Create Database」**

2. 填寫資料庫設定：

   | 欄位 | 建議值 | 說明 |
   |---|---|---|
   | **Name** | `happymeal-cache` | 名稱只作識別用途 |
   | **Type** | Regional | 單一 Region，延遲最低 |
   | **Region** | `AWS / ap-northeast-1 (Tokyo)` | 與 Lightsail 同區，延遲最小 |
   | **TLS** | 開啟（預設） | 連線加密，生產環境必須 |

3. 點擊 **「Create」**，資料庫建立約需 5–10 秒

> **為什麼選東京（ap-northeast-1）？**
> 如果 Lightsail 實例部署在東京，Upstash 也選東京，兩者之間的網路延遲可維持在 5–15 ms。
> 若選新加坡（ap-southeast-1），延遲約 30–50 ms，對快取的效益稍有折扣但仍可接受。
> 切勿選美國 Region，延遲將達 150ms 以上，失去快取的速度優勢。

---

## 四、取得連線字串

1. 建立完成後，點進剛建立的資料庫
2. 在 **「Details」** 頁籤找到 **「REST API」** 或 **「Connect」** 區塊
3. 找到 **`UPSTASH_REDIS_URL`** 或格式如下的連線字串：

   ```
   rediss://default:XXXXXXXXXXXXXXXX@your-db-name.upstash.io:6379
   ```

4. 點擊右側的複製圖示，將完整連線字串複製起來備用

### `rediss://` 與 `redis://` 的差別

| 前綴 | TLS 加密 | 適用情境 |
|---|---|---|
| `rediss://`（s 結尾） | ✅ 開啟 | 生產環境、任何跨公網的連線 |
| `redis://` | ❌ 未加密 | 本機 localhost 開發環境 |

Upstash 預設提供 `rediss://`（TLS），用於 Lightsail 連線時**不需要修改**，直接使用即可。

---

## 五、Lightsail 環境變數設定

根據你的 Lightsail 部署類型，操作方式略有不同。

### 方式 A：Lightsail Instance（虛擬機器）

若後端是以 SSH 登入實例、直接執行 Python 或 Docker Compose 的方式部署：

1. SSH 登入 Lightsail 實例
2. 編輯環境變數設定檔（視部署方式而定，通常是 `.env` 或 systemd service 的 `Environment` 欄位）
3. 新增以下一行：

   ```
   REDIS_URL=rediss://default:XXXXXXXXXXXXXXXX@your-db-name.upstash.io:6379
   ```

4. 重新啟動後端服務使設定生效

### 方式 B：Lightsail Container Service

若後端是以 Lightsail Container Service 部署：

1. 前往 AWS Lightsail Console → **「Containers」**
2. 點進你的 Container Service
3. 點擊 **「Deployments」** 頁籤
4. 點擊 **「Modify your deployment」**
5. 在 **「Environment variables」** 區塊點擊 **「Add」**
6. 填入：
   - Key：`REDIS_URL`
   - Value：貼上剛才複製的完整連線字串
7. 點擊 **「Save and deploy」**
8. 等待部署完成（通常需要 1–3 分鐘）

> **注意：** Lightsail Container Service 的環境變數設定後會觸發重新部署，舊版本 container 會自動替換為新版本，期間服務不會中斷（Rolling update）。

### 確認設定已生效

部署完成後，可以在 Lightsail Console 的 **「Deployments」→「Current version」** 下確認環境變數是否已出現在清單中（Value 會以 `***` 遮罩顯示）。

---

## 六、本機開發環境設定

本機開發時不需要連到 Upstash，改用本機的 Redis Container。

### 修改 `docker-compose.override.yml`

在本機開發專用的 override 檔案中新增 Redis 服務：

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 64mb --maxmemory-policy allkeys-lru
```

### 修改本機 `.env`

在本機開發用的 `.env` 檔案中加入：

```
REDIS_URL=redis://redis:6379/0
```

> **注意前綴：** 本機使用 `redis://`（無 TLS），因為是同一個 Docker network 內部的 localhost 連線。生產環境的 Upstash 則是 `rediss://`（有 TLS）。

### 啟動開發環境

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up
```

Redis 服務會和後端一起啟動，不需要額外設定。

---

## 七、驗證連線是否正常

### 方法一：Python 快速測試

在 Lightsail 實例（或本機）上執行以下指令：

```bash
python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'], decode_responses=True)
r.set('ping_test', 'ok', ex=60)
print('連線成功，寫入值：', r.get('ping_test'))
"
```

預期輸出：

```
連線成功，寫入值：ok
```

### 方法二：確認 Upstash Console 的請求計數

1. 回到 Upstash Console，點進 `happymeal-cache` 資料庫
2. 查看 **「Analytics」** 頁籤
3. 應可看到剛才的測試請求已被記錄（Request count 增加 2：一次 SET、一次 GET）

### 方法三：確認 RAG Cache 是否實際被寫入

上傳一張含蝦子的餐點圖並完成確認後，前往 Upstash Console 的 **「Data Browser」**，應該可以看到格式為 `rag:v1:xxxxxxxxxx` 的 Key。

---

## 八、費用說明與升級時機

### 免費方案的限制

| 項目 | 免費方案上限 |
|---|---|
| 每日請求數 | 10,000 次 |
| 資料庫大小 | 256 MB |
| 連線數 | 100 個並發連線 |
| 資料持久性 | 不保證（重啟可能清空） |

### 請求數估算（免費方案能撐多久）

每次 RAG Lookup：
- Cache Hit → 1 次 GET
- Cache Miss → 1 次 GET + 1 次 SET

假設：一餐 3 個食物、前 300 次查詢為 miss（暖機期），之後大多為 hit。

| 每日確認次數 | 每日 Redis 請求數（熱身後） | 是否超出免費方案 |
|---|---|---|
| 50 次 | ~150 次 | ✅ 安全 |
| 200 次 | ~600 次 | ✅ 安全 |
| 3,000 次 | ~9,000 次 | ⚠️ 接近上限 |

### 升級時機

當每日活躍使用者達到約 **500–1,000 人**時，建議升級至 Upstash 的 **Pay-as-you-go** 方案：

- 費用：$0.2 / 10 萬次請求（超出免費額度後才計費）
- 資料庫大小上限：按實際用量計費
- 資料持久性：保證（AOF 持久化）

升級只需在 Upstash Console 更改方案，**連線字串不需要修改**，程式碼和 Lightsail 環境變數完全不用動。
