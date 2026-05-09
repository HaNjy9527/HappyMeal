from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.food_mapping import NUTRITION_SOURCE_BY_MATCH_TYPE, resolve_canonical_food
from app.services.portion_resolution import quantize_decimal, resolve_nutrition_preset, resolve_portion


@dataclass(frozen=True)
class NutritionResolutionInput:
    food_name: str
    normalized_food_name: str
    portion_value: Decimal
    portion_unit: str
    confidence_score: Decimal | None = None


@dataclass(frozen=True)
class NutritionResolutionResult:
    food_name: str
    normalized_food_name: str
    portion_value: Decimal
    portion_unit: str
    source_portion_unit: str
    canonical_food_name: str
    nutrition_source: str
    is_estimated: bool
    resolved_weight_g: Decimal
    weight_estimation_method: str
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carb_g: Decimal
    confidence_score: Decimal | None = None


def resolve_item_nutrition(payload: NutritionResolutionInput) -> NutritionResolutionResult:
    resolved_food = resolve_canonical_food(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
    )
    nutrition_source = NUTRITION_SOURCE_BY_MATCH_TYPE[resolved_food.match_type]
    resolved_preset = resolve_nutrition_preset(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
        canonical_food_name=resolved_food.canonical_food_name,
        nutrition_source=nutrition_source,
        is_estimated=resolved_food.is_estimated,
    )
    portion_resolution = resolve_portion(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
        portion_unit=payload.portion_unit,
        portion_value=payload.portion_value,
        preset=resolved_preset.preset,
    )

    return NutritionResolutionResult(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
        portion_value=quantize_decimal(payload.portion_value),
        portion_unit=portion_resolution.portion_unit,
        source_portion_unit=portion_resolution.source_portion_unit,
        canonical_food_name=resolved_preset.canonical_food_name,
        nutrition_source=resolved_preset.nutrition_source,
        is_estimated=resolved_preset.is_estimated,
        resolved_weight_g=portion_resolution.resolved_weight_g,
        weight_estimation_method=portion_resolution.weight_estimation_method,
        kcal=quantize_decimal(resolved_preset.preset.kcal * portion_resolution.multiplier),
        protein_g=quantize_decimal(resolved_preset.preset.protein_g * portion_resolution.multiplier),
        fat_g=quantize_decimal(resolved_preset.preset.fat_g * portion_resolution.multiplier),
        carb_g=quantize_decimal(resolved_preset.preset.carb_g * portion_resolution.multiplier),
        confidence_score=payload.confidence_score,
    )
