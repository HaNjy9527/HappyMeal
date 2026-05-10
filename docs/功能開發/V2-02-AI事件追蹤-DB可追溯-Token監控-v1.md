# V2-02｜AI 事件追蹤：DB 可追溯 + Token 監控

- 文件名稱：V2-02｜AI 事件追蹤
- 版本：v1
- 日期：2026-05-10
- 狀態：規劃中
- 用途：把所有 AI 相關事件寫入 DB，補上 Token 用量追蹤，讓指標可用 SQL 分析

---

## 1. 目標

目前所有 AI 事件只寫入 stdout JSON log，若要分析歷史趨勢（例如「過去兩週的 Provider 錯誤率」或「不同 Prompt 版本的 candidate_count 分布」），需要人工在 AWS Lightsail log 介面逐筆閱讀，無法批量查詢。

本項目將在現有 log 基礎上，**額外**把關鍵 AI 事件寫入 PostgreSQL，讓任何指標都可以用 SQL 一行取出。Log 本身不動，DB 是額外的可查詢層。

同時補上目前缺少的 `input_tokens`、`output_tokens` 追蹤，讓每次 AI 呼叫的成本可量測。

---

## 2. 現況問題

| 問題 | 根因 |
|------|------|
| 無法批量查詢歷史 AI 指標 | 事件只在 log，沒有 DB |
| 不知道每次辨識花了多少 Token | `response.usage` 有資料但從未記錄 |
| Provider 錯誤率需人工閱讀 | log 沒有 query 介面 |
| Prompt 版本效果無法量測 | 無交叉分析基礎（等 V2-04 上線後才有意義）|

---

## 3. 不做的部分

- 不建獨立的 observability 資料庫或第三方監控平台
- 不做即時儀表板
- 不改動現有 stdout log 結構（保留，不刪）
- 不在 DB 寫入原始圖片或完整 prompt 內容

---

## 4. 技術設計

### 4-1 新增 Table：`ai_event_log`

```sql
CREATE TABLE ai_event_log (
    id                    VARCHAR(36)  PRIMARY KEY,
    user_id               VARCHAR(36)  REFERENCES users(id) ON DELETE SET NULL,
    analysis_id           VARCHAR(36)  REFERENCES food_analyses(id) ON DELETE SET NULL,
    event                 VARCHAR(50)  NOT NULL,
    outcome               VARCHAR(30),
    reason                VARCHAR(50),
    candidate_count       INTEGER,
    item_count            INTEGER,
    edited_item_count     INTEGER,
    manual_review_required BOOLEAN,
    has_instruction       BOOLEAN,
    used_fallback         BOOLEAN,
    input_tokens          INTEGER,
    output_tokens         INTEGER,
    prompt_version        VARCHAR(20),
    latency_ms            INTEGER,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

**欄位說明：**

| 欄位 | 填入的事件 |
|------|-----------|
| `event` | `openai_recognition`、`recognition_result`、`openai_reestimate`、`reestimate_result`、`analysis_upload`、`analysis_confirm` |
| `outcome` | `success`、`failure`、`partial`、`complete_failure` |
| `reason` | `quota_exceeded`、`provider_timeout`、`invalid_image`、`provider_unavailable`、`no_reliable_candidates` |
| `input_tokens` / `output_tokens` | 僅 `openai_recognition`、`openai_reestimate` |
| `prompt_version` | 待 V2-04 實作後開始填入 |
| `manual_review_required` | 僅 `recognition_result`、`reestimate_result` |
| `has_instruction` / `used_fallback` | 僅 `reestimate_result` |
| `item_count` / `edited_item_count` | 僅 `analysis_confirm` |

**索引：**
```sql
CREATE INDEX ix_ai_event_log_created_at ON ai_event_log (created_at);
CREATE INDEX ix_ai_event_log_event_outcome ON ai_event_log (event, outcome);
CREATE INDEX ix_ai_event_log_analysis_id ON ai_event_log (analysis_id);
```

---

### 4-2 呼叫鏈結構問題與解法

目前 `recognition_openai.py` 是純邏輯層，沒有 DB session，但 `input_tokens` 等 provider 層指標就在這裡產生。

**解法：讓 provider 層回傳 metrics dataclass，由有 DB session 的上層寫入。**

```
route handler
  → upload_analysis_image(db, ...)       ← 有 db，在這裡寫 DB
    → recognize_analysis_image(...)      ← 回傳結果含 provider metrics
      → recognize_meal_image_with_openai() ← 回傳 ProviderCallResult
        → request_openai_candidates()    ← 這裡取得 token 數，打包進 ProviderCallResult
```

**新增 `ProviderCallResult` dataclass：**

```python
# backend/app/services/recognition_openai.py

@dataclass(frozen=True)
class ProviderCallResult:
    candidates: list[ProviderCandidate]
    input_tokens: int
    output_tokens: int
    latency_ms: int
    outcome: str                  # "success" | "failure"
    reason: str | None = None     # 僅 failure 時填入
```

`request_openai_candidates()` 和 `request_openai_reestimate_candidates()` 的回傳型別從 `list[ProviderCandidate]` 改成 `ProviderCallResult`。

失敗路徑（except block）仍 raise `RecognitionProviderFailure`，但 exception 本身補上 `input_tokens`、`output_tokens`、`latency_ms` 欄位（目前只有 `reason` 和 `message`）。

---

### 4-3 新增 `AnalysisEventLog` Model

```python
# backend/app/db/models.py

class AnalysisEventLog(Base):
    __tablename__ = "ai_event_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    analysis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("food_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    event: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    candidate_count: Mapped[int | None] = mapped_column(nullable=True)
    item_count: Mapped[int | None] = mapped_column(nullable=True)
    edited_item_count: Mapped[int | None] = mapped_column(nullable=True)
    manual_review_required: Mapped[bool | None] = mapped_column(nullable=True)
    has_instruction: Mapped[bool | None] = mapped_column(nullable=True)
    used_fallback: Mapped[bool | None] = mapped_column(nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
```

---

### 4-4 寫入 Helper

```python
# backend/app/services/ai_event_log.py

import logging
from sqlalchemy.orm import Session
from app.db.models import AnalysisEventLog

logger = logging.getLogger("app.analysis")


def record_ai_event(
    db: Session,
    *,
    event: str,
    user_id: str | None = None,
    analysis_id: str | None = None,
    outcome: str | None = None,
    reason: str | None = None,
    candidate_count: int | None = None,
    item_count: int | None = None,
    edited_item_count: int | None = None,
    manual_review_required: bool | None = None,
    has_instruction: bool | None = None,
    used_fallback: bool | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    prompt_version: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """
    Best-effort DB write. 失敗不中斷主流程，只 log warning。
    """
    try:
        entry = AnalysisEventLog(
            event=event,
            user_id=user_id,
            analysis_id=analysis_id,
            outcome=outcome,
            reason=reason,
            candidate_count=candidate_count,
            item_count=item_count,
            edited_item_count=edited_item_count,
            manual_review_required=manual_review_required,
            has_instruction=has_instruction,
            used_fallback=used_fallback,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            prompt_version=prompt_version,
            latency_ms=latency_ms,
        )
        db.add(entry)
        db.flush()   # 寫入但不 commit，由呼叫方的 transaction 控制
    except Exception:
        logger.warning("Failed to write ai_event_log", exc_info=True)
```

**設計決策：**
- `db.flush()` 不 `commit()`：讓 DB write 跟著呼叫方的 transaction 一起 commit，若主流程 rollback，event log 也跟著 rollback（保持一致性）
- 外包 `try/except`：萬一 event log 寫入失敗，不中斷主要回應

---

### 4-5 各服務的呼叫點

**`analysis_upload.py`** — 寫入 `openai_recognition` + `recognition_result` + `analysis_upload`：

```python
# upload_analysis_image() 結尾，在 logger.info() 之後
record_ai_event(
    db,
    event="openai_recognition",
    user_id=user.id,
    analysis_id=analysis_id,
    outcome=provider_result.outcome,
    reason=provider_result.reason,
    candidate_count=len(provider_result.candidates),
    input_tokens=provider_result.input_tokens,
    output_tokens=provider_result.output_tokens,
    latency_ms=provider_result.provider_latency_ms,
)
record_ai_event(
    db,
    event="recognition_result",
    user_id=user.id,
    analysis_id=analysis_id,
    outcome=recognition_result.recognition_status.value,
    candidate_count=len(recognition_result.candidates),
    manual_review_required=recognition_result.manual_review_required,
)
record_ai_event(
    db,
    event="analysis_upload",
    user_id=user.id,
    analysis_id=analysis_id,
    outcome="success",
    latency_ms=latency_ms,
)
```

**`analysis_confirm.py`** — 寫入 `analysis_confirm`：

```python
record_ai_event(
    db,
    event="analysis_confirm",
    user_id=user.id,
    analysis_id=analysis_id,
    outcome="success",
    item_count=len(payload.items),
    edited_item_count=edited_item_count,
    latency_ms=latency_ms,
)
```

**`analysis_reestimate.py`** — 寫入 `openai_reestimate` + `reestimate_result`：（同樣模式）

---

## 5. 改動清單

| 檔案 | 改動內容 |
|------|---------|
| `backend/app/db/models.py` | 新增 `AnalysisEventLog` model |
| `backend/alembic/versions/xxxx_add_ai_event_log.py` | Migration：建立 `ai_event_log` 表與索引 |
| `backend/app/services/ai_event_log.py` | 新增 helper（`record_ai_event()`）|
| `backend/app/services/recognition_openai.py` | 新增 `ProviderCallResult` dataclass；`request_openai_candidates()` 和 `request_openai_reestimate_candidates()` 回傳型別改為 `ProviderCallResult`；`RecognitionProviderFailure` 補上 token 欄位 |
| `backend/app/services/analysis_recognition.py` | 接收 `ProviderCallResult`，把 provider metrics 傳回給上層 |
| `backend/app/services/analysis_upload.py` | 呼叫 `record_ai_event()` 三次（openai_recognition、recognition_result、analysis_upload）|
| `backend/app/services/analysis_confirm.py` | 呼叫 `record_ai_event()` 一次（analysis_confirm）|
| `backend/app/services/analysis_reestimate.py` | 呼叫 `record_ai_event()` 兩次（openai_reestimate、reestimate_result）|

---

## 6. 常用查詢範例

```sql
-- 每日平均辨識延遲
SELECT DATE(created_at), AVG(latency_ms)
FROM ai_event_log
WHERE event = 'openai_recognition'
GROUP BY 1 ORDER BY 1;

-- Provider 錯誤率與分布
SELECT reason, COUNT(*) AS cnt,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM ai_event_log
WHERE event = 'openai_recognition' AND outcome = 'failure'
GROUP BY reason;

-- 人工審查觸發率趨勢（週）
SELECT DATE_TRUNC('week', created_at) AS week,
       AVG(CASE WHEN manual_review_required THEN 1.0 ELSE 0.0 END) AS fallback_rate
FROM ai_event_log
WHERE event = 'recognition_result'
GROUP BY 1 ORDER BY 1;

-- 每次分析的 Token 成本
SELECT analysis_id,
       SUM(input_tokens)  AS total_input_tokens,
       SUM(output_tokens) AS total_output_tokens,
       SUM(input_tokens + output_tokens) AS total_tokens
FROM ai_event_log
WHERE analysis_id IS NOT NULL
GROUP BY analysis_id;

-- Prompt 版本 A/B 比較（V2-04 上線後才有資料）
SELECT prompt_version,
       COUNT(*) AS calls,
       AVG(candidate_count) AS avg_candidates,
       AVG(CASE WHEN outcome = 'success' THEN 1.0 ELSE 0.0 END) AS success_rate
FROM ai_event_log
WHERE event = 'openai_recognition'
GROUP BY prompt_version;

-- 使用者修改率（edited_item_count > 0 的比例）
SELECT DATE(created_at),
       AVG(CASE WHEN edited_item_count > 0 THEN 1.0 ELSE 0.0 END) AS edit_rate,
       AVG(edited_item_count::float / NULLIF(item_count, 0)) AS avg_edit_ratio
FROM ai_event_log
WHERE event = 'analysis_confirm'
GROUP BY 1 ORDER BY 1;
```

---

## 7. 驗收條件

1. Alembic migration 可正常 `upgrade` 與 `downgrade`
2. 完成一次 analysis 流程後，`ai_event_log` 至少寫入 3 筆（`openai_recognition`、`recognition_result`、`analysis_upload`）
3. 完成 confirm 後再多 1 筆（`analysis_confirm`）
4. `input_tokens`、`output_tokens` 在 `openai_recognition` 事件中不為 NULL
5. Provider 錯誤（例如 timeout）發生時，`outcome = 'failure'`、`reason` 正確填入
6. 寫入失敗時（模擬 DB 錯誤），主流程 response 不受影響，只寫一條 warning log
7. 現有 85 個測試全過（新 model 不影響現有邏輯）

---

## 8. 相關文件

- 路線圖：[Roadmap-v2-v3-概覽.md](./Roadmap-v2-v3-%E6%A6%82%E8%A6%BD.md)
- 現有 log 結構：[Priority5-觀測性與效能基線-v1.md](./Priority5-%E8%A7%80%E6%B8%AC%E6%80%A7%E8%88%87%E6%95%88%E8%83%BD%E5%9F%BA%E7%B7%9A-v1.md)
