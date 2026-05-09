from __future__ import annotations

import re

from dataclasses import dataclass
from decimal import Decimal

from app.services.portion_resolution import NutritionPreset


@dataclass(frozen=True)
class OfficialNutritionRecord:
    canonical_food_name: str
    aliases: tuple[str, ...]
    preset: NutritionPreset
    source: str = "official_source"
    source_label: str = "curated_mvp_v1"


OFFICIAL_NUTRITION_CATALOG = {
    "black_coffee": OfficialNutritionRecord(
        canonical_food_name="black_coffee",
        aliases=("black_coffee", "americano", "unsweetened_coffee"),
        preset=NutritionPreset(
            "g",
            Decimal("100.00"),
            Decimal("2.00"),
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.50"),
        ),
    ),
    "white_rice": OfficialNutritionRecord(
        canonical_food_name="white_rice",
        aliases=("white_rice", "generic_rice"),
        preset=NutritionPreset(
            "bowl",
            Decimal("160.00"),
            Decimal("216.00"),
            Decimal("5.00"),
            Decimal("1.80"),
            Decimal("45.00"),
        ),
    ),
    "boiled_egg": OfficialNutritionRecord(
        canonical_food_name="boiled_egg",
        aliases=("boiled_egg",),
        preset=NutritionPreset(
            "pcs",
            Decimal("50.00"),
            Decimal("78.00"),
            Decimal("6.50"),
            Decimal("5.30"),
            Decimal("0.60"),
        ),
    ),
    "chicken_breast": OfficialNutritionRecord(
        canonical_food_name="chicken_breast",
        aliases=("chicken_breast", "grilled_chicken_breast"),
        preset=NutritionPreset(
            "g",
            Decimal("100.00"),
            Decimal("165.00"),
            Decimal("31.00"),
            Decimal("3.60"),
            Decimal("0.00"),
        ),
    ),
    "leafy_vegetables": OfficialNutritionRecord(
        canonical_food_name="leafy_vegetables",
        aliases=("leafy_vegetables",),
        preset=NutritionPreset(
            "g",
            Decimal("100.00"),
            Decimal("35.00"),
            Decimal("2.00"),
            Decimal("0.50"),
            Decimal("6.00"),
        ),
    ),
}


def normalize_catalog_hint(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[_\-]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized)


def lookup_official_nutrition(
    *,
    food_name: str,
    normalized_food_name: str,
    canonical_food_name: str | None = None,
) -> OfficialNutritionRecord | None:
    direct_keys = (normalized_food_name, canonical_food_name)
    for key in direct_keys:
        if key and key in OFFICIAL_NUTRITION_CATALOG:
            return OFFICIAL_NUTRITION_CATALOG[key]

    hints = {
        normalize_catalog_hint(food_name),
        normalize_catalog_hint(normalized_food_name),
    }
    if canonical_food_name:
        hints.add(normalize_catalog_hint(canonical_food_name))

    for record in OFFICIAL_NUTRITION_CATALOG.values():
        alias_hints = {normalize_catalog_hint(alias) for alias in record.aliases}
        if hints & alias_hints:
            return record

    return None
