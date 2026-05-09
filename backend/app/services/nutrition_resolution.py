from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.food_mapping import NUTRITION_SOURCE_BY_MATCH_TYPE, resolve_canonical_food
from app.services.portion_resolution import (
    NUTRITION_PRESETS,
    NutritionPreset,
    is_packaged_drink,
    quantize_decimal,
    resolve_portion,
)


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


@dataclass(frozen=True)
class NutritionSourceCandidate:
    source: str
    canonical_food_name: str
    is_estimated: bool
    preset: NutritionPreset | None
    matched: bool


@dataclass(frozen=True)
class NutritionSourceResolution:
    candidate: NutritionSourceCandidate
    priority: str


@dataclass(frozen=True)
class NutritionSourceDecision:
    source: str
    canonical_food_name: str
    is_estimated: bool
    preset: NutritionPreset
    priority: str


def resolve_official_source(payload: NutritionResolutionInput) -> NutritionSourceCandidate:
    return NutritionSourceCandidate(
        source="official_source",
        canonical_food_name=payload.normalized_food_name,
        is_estimated=False,
        preset=None,
        matched=False,
    )


def resolve_canonical_mapping_source(payload: NutritionResolutionInput) -> NutritionSourceCandidate:
    resolved_food = resolve_canonical_food(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
    )
    nutrition_source = NUTRITION_SOURCE_BY_MATCH_TYPE[resolved_food.match_type]
    preset = NUTRITION_PRESETS.get(resolved_food.canonical_food_name)
    matched = resolved_food.match_type != "default_fallback" and preset is not None

    return NutritionSourceCandidate(
        source=nutrition_source,
        canonical_food_name=resolved_food.canonical_food_name,
        is_estimated=resolved_food.is_estimated,
        preset=preset if matched else None,
        matched=matched,
    )


def resolve_fallback_source(_: NutritionResolutionInput) -> NutritionSourceCandidate:
    return NutritionSourceCandidate(
        source="default_fallback",
        canonical_food_name="generic_mixed_meal",
        is_estimated=True,
        preset=NUTRITION_PRESETS["generic_mixed_meal"],
        matched=True,
    )


def apply_special_source_guards(
    payload: NutritionResolutionInput,
    resolution: NutritionSourceResolution,
) -> NutritionSourceResolution:
    if (
        is_packaged_drink(
            food_name=payload.food_name,
            normalized_food_name=payload.normalized_food_name,
        )
        and resolution.candidate.canonical_food_name == "generic_mixed_meal"
    ):
        return NutritionSourceResolution(
            candidate=NutritionSourceCandidate(
                source="drink_fallback",
                canonical_food_name="generic_unsweetened_drink",
                is_estimated=True,
                preset=NUTRITION_PRESETS["generic_unsweetened_drink"],
                matched=True,
            ),
            priority="special_guard",
        )

    return resolution


def select_nutrition_source(payload: NutritionResolutionInput) -> NutritionSourceDecision:
    official_source = resolve_official_source(payload)
    if official_source.matched:
        selected = NutritionSourceResolution(candidate=official_source, priority="official_source")
    else:
        canonical_mapping = resolve_canonical_mapping_source(payload)
        if canonical_mapping.matched:
            selected = NutritionSourceResolution(candidate=canonical_mapping, priority="canonical_mapping")
        else:
            selected = NutritionSourceResolution(
                candidate=resolve_fallback_source(payload),
                priority="fallback_estimate",
            )

    selected = apply_special_source_guards(payload, selected)
    if selected.candidate.preset is None:
        selected = NutritionSourceResolution(
            candidate=resolve_fallback_source(payload),
            priority="fallback_estimate",
        )

    return NutritionSourceDecision(
        source=selected.candidate.source,
        canonical_food_name=selected.candidate.canonical_food_name,
        is_estimated=selected.candidate.is_estimated,
        preset=selected.candidate.preset,
        priority=selected.priority,
    )


def resolve_item_nutrition(payload: NutritionResolutionInput) -> NutritionResolutionResult:
    source_decision = select_nutrition_source(payload)
    portion_resolution = resolve_portion(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
        portion_unit=payload.portion_unit,
        portion_value=payload.portion_value,
        preset=source_decision.preset,
    )

    return NutritionResolutionResult(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
        portion_value=quantize_decimal(payload.portion_value),
        portion_unit=portion_resolution.portion_unit,
        source_portion_unit=portion_resolution.source_portion_unit,
        canonical_food_name=source_decision.canonical_food_name,
        nutrition_source=source_decision.source,
        is_estimated=source_decision.is_estimated,
        resolved_weight_g=portion_resolution.resolved_weight_g,
        weight_estimation_method=portion_resolution.weight_estimation_method,
        kcal=quantize_decimal(source_decision.preset.kcal * portion_resolution.multiplier),
        protein_g=quantize_decimal(source_decision.preset.protein_g * portion_resolution.multiplier),
        fat_g=quantize_decimal(source_decision.preset.fat_g * portion_resolution.multiplier),
        carb_g=quantize_decimal(source_decision.preset.carb_g * portion_resolution.multiplier),
        confidence_score=payload.confidence_score,
    )
