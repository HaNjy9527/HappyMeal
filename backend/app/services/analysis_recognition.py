from __future__ import annotations

from pathlib import Path

from app.schemas.analysis import AnalysisCandidateItem
from app.services.recognition_normalization import normalize_provider_candidates
from app.services.recognition_openai import recognize_meal_image_with_openai


def recognize_analysis_image(*, filename: str | None, image_path: Path) -> list[AnalysisCandidateItem]:
    provider_candidates = recognize_meal_image_with_openai(filename=filename, image_path=image_path)
    return normalize_provider_candidates(provider_candidates)