from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.services.recognition_provider import ProviderCandidate


MOCK_CANDIDATE_PRESETS = {
    "salad": [
        ProviderCandidate(
            food_name="Chicken Salad",
            normalized_food_name="chicken_salad",
            confidence_score=Decimal("0.942"),
            portion_default=Decimal("1.00"),
            portion_unit="bowl",
        ),
        ProviderCandidate(
            food_name="Boiled Egg",
            normalized_food_name="boiled_egg",
            confidence_score=Decimal("0.811"),
            portion_default=Decimal("1.00"),
            portion_unit="pcs",
        ),
    ],
    "rice": [
        ProviderCandidate(
            food_name="Grilled Chicken Rice",
            normalized_food_name="grilled_chicken_rice",
            confidence_score=Decimal("0.918"),
            portion_default=Decimal("1.00"),
            portion_unit="plate",
        ),
        ProviderCandidate(
            food_name="Stir-fried Vegetables",
            normalized_food_name="stir_fried_vegetables",
            confidence_score=Decimal("0.768"),
            portion_default=Decimal("0.50"),
            portion_unit="plate",
        ),
    ],
}

DEFAULT_PROVIDER_CANDIDATES = [
    ProviderCandidate(
        food_name="Grilled Salmon",
        normalized_food_name="grilled_salmon",
        confidence_score=Decimal("0.903"),
        portion_default=Decimal("1.00"),
        portion_unit="fillet",
    ),
    ProviderCandidate(
        food_name="Brown Rice",
        normalized_food_name="brown_rice",
        confidence_score=Decimal("0.845"),
        portion_default=Decimal("1.00"),
        portion_unit="bowl",
    ),
    ProviderCandidate(
        food_name="Steamed Broccoli",
        normalized_food_name="steamed_broccoli",
        confidence_score=Decimal("0.732"),
        portion_default=Decimal("0.50"),
        portion_unit="bowl",
    ),
]


def recognize_meal_image_with_openai(*, filename: str | None, image_path: Path) -> list[ProviderCandidate]:
    if filename:
        normalized_filename = filename.lower()

        if "salad" in normalized_filename:
            return MOCK_CANDIDATE_PRESETS["salad"]

        if "rice" in normalized_filename:
            return MOCK_CANDIDATE_PRESETS["rice"]

    return DEFAULT_PROVIDER_CANDIDATES