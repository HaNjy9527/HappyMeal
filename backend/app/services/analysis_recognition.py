from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.schemas.analysis import AnalysisCandidateItem, RecognitionStatus
from app.services.recognition_normalization import normalize_provider_candidates
from app.services.recognition_openai import ProviderCallResult, RecognitionProviderFailure, recognize_meal_image_with_openai


PARTIAL_CONFIDENCE_THRESHOLD = Decimal("0.6")

logger = logging.getLogger("app.analysis")


@dataclass(slots=True)
class AnalysisRecognitionResult:
    recognition_status: RecognitionStatus
    candidates: list[AnalysisCandidateItem]
    manual_review_required: bool = False
    fallback_reason: str | None = None
    message: str | None = None
    # Provider 層指標，供上層寫 ai_event_log
    provider_input_tokens: int | None = None
    provider_output_tokens: int | None = None
    provider_latency_ms: int = 0
    provider_outcome: str = "success"   # "success" | "failure"
    provider_reason: str | None = None


def recognize_analysis_image(*, filename: str | None, image_path: Path) -> AnalysisRecognitionResult:
    try:
        provider_result: ProviderCallResult = recognize_meal_image_with_openai(filename=filename, image_path=image_path)
    except RecognitionProviderFailure as error:
        logger.warning(
            "Recognition complete_failure from provider",
            extra={"event": "recognition_result", "outcome": "complete_failure", "reason": error.reason, "candidate_count": 0, "manual_review_required": False},
        )
        return AnalysisRecognitionResult(
            recognition_status=RecognitionStatus.COMPLETE_FAILURE,
            candidates=[],
            manual_review_required=False,
            fallback_reason=error.reason,
            message=error.message,
            provider_latency_ms=error.latency_ms,
            provider_outcome="failure",
            provider_reason=error.reason,
        )

    candidates = normalize_provider_candidates(provider_result.candidates)
    if candidates:
        has_low_confidence = any(c.confidence_score < PARTIAL_CONFIDENCE_THRESHOLD for c in candidates)
        if has_low_confidence:
            logger.info(
                "Recognition partial",
                extra={"event": "recognition_result", "outcome": "partial", "candidate_count": len(candidates), "manual_review_required": True},
            )
            return AnalysisRecognitionResult(
                recognition_status=RecognitionStatus.PARTIAL,
                candidates=candidates,
                manual_review_required=True,
                message="AI 對部分食物辨識信心不足，請確認或修正後再送出。",
                provider_input_tokens=provider_result.input_tokens,
                provider_output_tokens=provider_result.output_tokens,
                provider_latency_ms=provider_result.latency_ms,
                provider_outcome=provider_result.outcome,
            )
        logger.info(
            "Recognition success",
            extra={"event": "recognition_result", "outcome": "success", "candidate_count": len(candidates), "manual_review_required": False},
        )
        return AnalysisRecognitionResult(
            recognition_status=RecognitionStatus.SUCCESS,
            candidates=candidates,
            provider_input_tokens=provider_result.input_tokens,
            provider_output_tokens=provider_result.output_tokens,
            provider_latency_ms=provider_result.latency_ms,
            provider_outcome=provider_result.outcome,
        )

    logger.warning(
        "Recognition complete_failure no reliable candidates",
        extra={"event": "recognition_result", "outcome": "complete_failure", "reason": "no_reliable_candidates", "candidate_count": 0, "manual_review_required": False},
    )
    return AnalysisRecognitionResult(
        recognition_status=RecognitionStatus.COMPLETE_FAILURE,
        candidates=[],
        manual_review_required=False,
        fallback_reason="no_reliable_candidates",
        message="AI 這次沒有穩定辨識出食物，請重拍或換一張更清楚的圖片。",
        provider_input_tokens=provider_result.input_tokens,
        provider_output_tokens=provider_result.output_tokens,
        provider_latency_ms=provider_result.latency_ms,
        provider_outcome=provider_result.outcome,
    )
