from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.schemas.analysis import AnalysisCandidateItem, RecognitionStatus
from app.services.recognition_normalization import normalize_provider_candidates
from app.services.recognition_openai import RecognitionProviderFailure, recognize_meal_image_with_openai


@dataclass(slots=True)
class AnalysisRecognitionResult:
    recognition_status: RecognitionStatus
    candidates: list[AnalysisCandidateItem]
    manual_review_required: bool = False
    fallback_reason: str | None = None
    message: str | None = None


def recognize_analysis_image(*, filename: str | None, image_path: Path) -> AnalysisRecognitionResult:
    try:
        provider_candidates = recognize_meal_image_with_openai(filename=filename, image_path=image_path)
    except RecognitionProviderFailure as error:
        return AnalysisRecognitionResult(
            recognition_status=RecognitionStatus.COMPLETE_FAILURE,
            candidates=[],
            manual_review_required=False,
            fallback_reason=error.reason,
            message=error.message,
        )

    candidates = normalize_provider_candidates(provider_candidates)
    if candidates:
        return AnalysisRecognitionResult(
            recognition_status=RecognitionStatus.SUCCESS,
            candidates=candidates,
        )

    return AnalysisRecognitionResult(
        recognition_status=RecognitionStatus.COMPLETE_FAILURE,
        candidates=[],
        manual_review_required=False,
        fallback_reason="no_reliable_candidates",
        message="AI 這次沒有穩定辨識出食物，請重拍或換一張更清楚的圖片。",
    )