"""
V2-02：AI 事件寫入 helper

Best-effort：寫入失敗只記 warning，不中斷主流程。
使用 db.flush()（不 commit），讓 event 跟著呼叫方的 transaction 一起提交或 rollback。
"""

from __future__ import annotations

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
    manual_review_required: bool | None = None,
    has_instruction: bool | None = None,
    used_fallback: bool | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    prompt_version: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """Best-effort DB write。失敗不中斷主流程，只寫 warning log。"""
    try:
        entry = AnalysisEventLog(
            event=event,
            user_id=user_id,
            analysis_id=analysis_id,
            outcome=outcome,
            reason=reason,
            candidate_count=candidate_count,
            item_count=item_count,
            manual_review_required=manual_review_required,
            has_instruction=has_instruction,
            used_fallback=used_fallback,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            prompt_version=prompt_version,
            latency_ms=latency_ms,
        )
        db.add(entry)
        db.flush()
    except Exception:
        logger.warning("Failed to write ai_event_log", exc_info=True)
