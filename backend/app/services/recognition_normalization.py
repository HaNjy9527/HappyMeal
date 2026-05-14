from __future__ import annotations

from decimal import Decimal

from app.schemas.analysis import AnalysisCandidateItem
from app.services.recognition_provider import ProviderCandidate


DEFAULT_PORTION_UNIT = "serving"
DEFAULT_PORTION_VALUE = Decimal("1.00")


def normalize_provider_candidates(candidates: list[ProviderCandidate]) -> list[AnalysisCandidateItem]:
    normalized_candidates: list[AnalysisCandidateItem] = []

    for candidate in candidates:
        food_name = candidate.food_name.strip()
        normalized_food_name = candidate.normalized_food_name.strip()

        if not food_name or not normalized_food_name:
            continue

        portion_unit = candidate.portion_unit.strip() or DEFAULT_PORTION_UNIT
        portion_default = candidate.portion_default if candidate.portion_default > 0 else DEFAULT_PORTION_VALUE

        normalized_candidates.append(
            AnalysisCandidateItem(
                food_name=food_name,
                normalized_food_name=normalized_food_name,
                confidence_score=candidate.confidence_score,
                portion_default=portion_default,
                portion_unit=portion_unit,
                food_type=candidate.food_type,
            )
        )

    return normalized_candidates