from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import AnalysisStatus, User
from app.schemas.analysis import (
    AnalysisCandidateItem,
    AnalysisReestimateRequest,
    AnalysisReestimateResponse,
    RecognitionStatus,
)
from app.services.analysis import get_analysis_for_user
from app.services.recognition_normalization import normalize_provider_candidates
from app.services.recognition_openai import (
    RecognitionProviderFailure,
    reestimate_meal_items_with_openai,
)
from app.services.recognition_provider import ProviderCandidate


def build_items_payload(payload: AnalysisReestimateRequest) -> list[dict[str, object]]:
    return [
        {
            "food_name": item.food_name,
            "normalized_food_name": item.normalized_food_name,
            "portion_value": str(item.portion_value),
            "portion_unit": item.portion_unit,
            "confidence_score": str(item.confidence_score) if item.confidence_score is not None else None,
            "is_user_edited": item.is_user_edited,
        }
        for item in payload.items
    ]


def build_fallback_candidates(payload: AnalysisReestimateRequest) -> list[ProviderCandidate]:
    portion_multiplier = Decimal("0.50") if payload.user_instruction and "半份" in payload.user_instruction else Decimal("1.00")

    return [
        ProviderCandidate(
            food_name=item.food_name,
            normalized_food_name=item.normalized_food_name,
            confidence_score=item.confidence_score or Decimal("0.70"),
            portion_default=item.portion_value * portion_multiplier,
            portion_unit=item.portion_unit,
        )
        for item in payload.items
    ]


def reestimate_analysis(
    db: Session,
    user: User,
    analysis_id: str,
    payload: AnalysisReestimateRequest,
) -> AnalysisReestimateResponse:
    analysis = get_analysis_for_user(db, user, analysis_id)
    if analysis.status != AnalysisStatus.AWAITING_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="AI re-estimation is only allowed for analyses awaiting confirmation",
        )

    items_payload = build_items_payload(payload)
    try:
        provider_candidates = reestimate_meal_items_with_openai(
            items_payload=items_payload,
            user_instruction=payload.user_instruction,
        )
    except RecognitionProviderFailure as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error.message,
        ) from error

    if not provider_candidates:
        provider_candidates = build_fallback_candidates(payload)

    candidates = normalize_provider_candidates(provider_candidates)
    recognition_status = RecognitionStatus.PARTIAL if payload.user_instruction else RecognitionStatus.SUCCESS
    message = "AI 已根據你目前的修正重新估算，請再次確認名稱和份量。"
    if payload.user_instruction:
        message = "AI 已根據你的備註重新估算，請再次確認名稱和份量。"

    return AnalysisReestimateResponse(
        analysis_id=analysis.id,
        recognition_status=recognition_status,
        message=message,
        candidates=[AnalysisCandidateItem.model_validate(candidate) for candidate in candidates],
        fallback_reason=None,
    )