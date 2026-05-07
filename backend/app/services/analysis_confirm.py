from __future__ import annotations

import json

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import AnalysisStatus, ExerciseCatalog, FoodAnalysisItem, GoalType, RecommendationSnapshot, User
from app.schemas.analysis import (
    AnalysisConfirmItemRequest,
    AnalysisConfirmRequest,
    AnalysisConfirmResponse,
    RecommendedExerciseItem,
)
from app.services.analysis import get_analysis_for_user
from app.services.food_mapping import NUTRITION_SOURCE_BY_MATCH_TYPE, resolve_canonical_food
from app.services.analysis_upload import delete_analysis_uploads
from app.services.consent import build_non_medical_disclaimer
from app.services.profile import get_or_create_profile
from app.services.analysis_views import build_analysis_result_items, build_recommendation_response


TWOPLACES = Decimal("0.01")
ZERO_DECIMAL = Decimal("0.00")
PERSONALIZED_RECOMMENDATION_SOURCE = "personalized"
GENERIC_RECOMMENDATION_SOURCE = "generic"
ACTIVITY_MULTIPLIERS = {
    "sedentary": Decimal("1.20"),
    "light": Decimal("1.35"),
    "moderate": Decimal("1.50"),
    "active": Decimal("1.65"),
    "very_active": Decimal("1.80"),
}
GOAL_CALORIE_ADJUSTMENTS = {
    GoalType.MUSCLE_GAIN: Decimal("250"),
    GoalType.FAT_LOSS: Decimal("-300"),
}
PROTEIN_MULTIPLIERS = {
    GoalType.MUSCLE_GAIN: Decimal("1.80"),
    GoalType.FAT_LOSS: Decimal("1.60"),
}
FAT_MULTIPLIERS = {
    GoalType.MUSCLE_GAIN: Decimal("0.80"),
    GoalType.FAT_LOSS: Decimal("0.70"),
}
PREFERRED_EXERCISE_CATEGORY = {
    GoalType.MUSCLE_GAIN: "strength",
    GoalType.FAT_LOSS: "cardio",
}
EXERCISE_DURATIONS = [20, 30, 40]
GENERIC_TARGET_CALORIES = Decimal("2000.00")
GENERIC_TARGET_PROTEIN = Decimal("110.00")
GENERIC_TARGET_FAT = Decimal("60.00")
GENERIC_EXERCISE_BURN_ESTIMATES = [Decimal("90.00"), Decimal("140.00"), Decimal("190.00")]


@dataclass(frozen=True)
class NutritionPreset:
    portion_unit: str
    portion_weight_g: Decimal
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carb_g: Decimal


@dataclass(frozen=True)
class ResolvedNutritionPreset:
    canonical_food_name: str
    nutrition_source: str
    is_estimated: bool
    preset: NutritionPreset


@dataclass(frozen=True)
class PortionResolution:
    source_portion_unit: str
    portion_unit: str
    resolved_weight_g: Decimal
    weight_estimation_method: str
    multiplier: Decimal


NUTRITION_PRESETS = {
    "chicken_salad": NutritionPreset("bowl", Decimal("280.00"), Decimal("320.00"), Decimal("28.00"), Decimal("18.00"), Decimal("12.00")),
    "boiled_egg": NutritionPreset("pcs", Decimal("50.00"), Decimal("78.00"), Decimal("6.50"), Decimal("5.30"), Decimal("0.60")),
    "grilled_chicken_rice": NutritionPreset("plate", Decimal("360.00"), Decimal("520.00"), Decimal("34.00"), Decimal("12.00"), Decimal("63.00")),
    "stir_fried_vegetables": NutritionPreset("plate", Decimal("250.00"), Decimal("160.00"), Decimal("5.00"), Decimal("7.00"), Decimal("18.00")),
    "grilled_salmon": NutritionPreset("fillet", Decimal("150.00"), Decimal("280.00"), Decimal("26.00"), Decimal("18.00"), Decimal("0.00")),
    "brown_rice": NutritionPreset("bowl", Decimal("160.00"), Decimal("216.00"), Decimal("5.00"), Decimal("1.80"), Decimal("45.00")),
    "steamed_broccoli": NutritionPreset("bowl", Decimal("90.00"), Decimal("55.00"), Decimal("3.70"), Decimal("0.60"), Decimal("11.00")),
    "generic_mixed_meal": NutritionPreset("bowl", Decimal("320.00"), Decimal("420.00"), Decimal("20.00"), Decimal("14.00"), Decimal("52.00")),
    "generic_rice": NutritionPreset("bowl", Decimal("160.00"), Decimal("216.00"), Decimal("5.00"), Decimal("1.80"), Decimal("45.00")),
    "generic_vegetables": NutritionPreset("bowl", Decimal("100.00"), Decimal("60.00"), Decimal("3.00"), Decimal("0.80"), Decimal("10.00")),
    "generic_condiment": NutritionPreset("tbsp", Decimal("15.00"), Decimal("35.00"), Decimal("0.50"), Decimal("2.00"), Decimal("3.00")),
    "generic_garnish": NutritionPreset("tbsp", Decimal("6.00"), Decimal("8.00"), Decimal("0.20"), Decimal("0.10"), Decimal("1.50")),
    "generic_protein": NutritionPreset("plate", Decimal("180.00"), Decimal("260.00"), Decimal("26.00"), Decimal("14.00"), Decimal("4.00")),
}

UNIT_ALIASES = {
    "plates": "plate",
    "dish": "plate",
    "dishes": "plate",
    "bowls": "bowl",
    "cups": "cup",
    "servings": "serving",
    "portion": "serving",
    "portions": "serving",
    "pieces": "pcs",
    "piece": "pcs",
    "pc": "pcs",
    "fillets": "fillet",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "spoon": "tbsp",
    "spoons": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "bags": "bag",
    "boxes": "box",
}
UNIT_FAMILIES = {
    "container": {
        "plate": Decimal("1.00"),
        "bowl": Decimal("0.90"),
        "box": Decimal("1.00"),
        "bag": Decimal("1.00"),
        "cup": Decimal("0.75"),
        "serving": Decimal("1.00"),
    },
    "piece": {
        "pcs": Decimal("1.00"),
        "fillet": Decimal("1.00"),
    },
    "spoon": {
        "tbsp": Decimal("1.00"),
        "tsp": Decimal("0.33"),
    },
}
def quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def has_complete_recommendation_profile(profile) -> bool:
    return (
        profile.weight_kg is not None
        and profile.activity_level is not None
        and profile.goal_type is not None
    )


def normalize_portion_unit(unit: str) -> str:
    normalized_unit = unit.strip().lower()
    return UNIT_ALIASES.get(normalized_unit, normalized_unit)


def build_resolved_preset(canonical_food_name: str, nutrition_source: str, is_estimated: bool) -> ResolvedNutritionPreset:
    return ResolvedNutritionPreset(
        canonical_food_name=canonical_food_name,
        nutrition_source=nutrition_source,
        is_estimated=is_estimated,
        preset=NUTRITION_PRESETS[canonical_food_name],
    )


def resolve_food_preset(payload: AnalysisConfirmItemRequest) -> ResolvedNutritionPreset:
    resolved_food = resolve_canonical_food(
        food_name=payload.food_name,
        normalized_food_name=payload.normalized_food_name,
    )
    nutrition_source = NUTRITION_SOURCE_BY_MATCH_TYPE[resolved_food.match_type]
    return build_resolved_preset(
        resolved_food.canonical_food_name,
        nutrition_source,
        resolved_food.is_estimated,
    )


def resolve_portion(payload: AnalysisConfirmItemRequest, preset: NutritionPreset) -> PortionResolution:
    source_portion_unit = payload.portion_unit.strip()
    normalized_unit = normalize_portion_unit(source_portion_unit)
    portion_value = quantize_decimal(payload.portion_value)

    if normalized_unit == "g":
        resolved_weight_g = quantize_decimal(portion_value)
        multiplier = quantize_decimal(resolved_weight_g / preset.portion_weight_g)
        return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "direct_grams", multiplier)

    if normalized_unit == preset.portion_unit:
        resolved_weight_g = quantize_decimal(preset.portion_weight_g * portion_value)
        return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "exact_unit_match", portion_value)

    for family_units in UNIT_FAMILIES.values():
        requested_weight = family_units.get(normalized_unit)
        canonical_weight = family_units.get(preset.portion_unit)
        if requested_weight is None or canonical_weight is None:
            continue

        ratio = quantize_decimal(requested_weight / canonical_weight)
        multiplier = quantize_decimal(portion_value * ratio)
        resolved_weight_g = quantize_decimal(preset.portion_weight_g * multiplier)
        return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "common_unit_conversion", multiplier)

    resolved_weight_g = quantize_decimal(preset.portion_weight_g * portion_value)
    return PortionResolution(source_portion_unit, normalized_unit, resolved_weight_g, "assumed_common_serving_weight", portion_value)


def build_analysis_item(payload: AnalysisConfirmItemRequest) -> FoodAnalysisItem:
    resolved_preset = resolve_food_preset(payload)
    portion_resolution = resolve_portion(payload, resolved_preset.preset)

    return FoodAnalysisItem(
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
        confidence_score=payload.confidence_score,
        kcal=quantize_decimal(resolved_preset.preset.kcal * portion_resolution.multiplier),
        protein_g=quantize_decimal(resolved_preset.preset.protein_g * portion_resolution.multiplier),
        fat_g=quantize_decimal(resolved_preset.preset.fat_g * portion_resolution.multiplier),
        carb_g=quantize_decimal(resolved_preset.preset.carb_g * portion_resolution.multiplier),
    )


def calculate_targets(weight_kg: Decimal, activity_level: str, goal_type: GoalType) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    base_calories = weight_kg * Decimal("30")
    target_calories = quantize_decimal(base_calories * ACTIVITY_MULTIPLIERS[activity_level] + GOAL_CALORIE_ADJUSTMENTS[goal_type])
    target_protein = quantize_decimal(weight_kg * PROTEIN_MULTIPLIERS[goal_type])
    target_fat = quantize_decimal(weight_kg * FAT_MULTIPLIERS[goal_type])
    remaining_calories = target_calories - (target_protein * Decimal("4")) - (target_fat * Decimal("9"))
    target_carb = quantize_decimal(max(remaining_calories / Decimal("4"), ZERO_DECIMAL))
    return target_calories, target_protein, target_fat, target_carb


def build_generic_targets() -> tuple[Decimal, Decimal, Decimal, Decimal]:
    remaining_calories = (
        GENERIC_TARGET_CALORIES
        - (GENERIC_TARGET_PROTEIN * Decimal("4"))
        - (GENERIC_TARGET_FAT * Decimal("9"))
    )
    target_carb = quantize_decimal(max(remaining_calories / Decimal("4"), ZERO_DECIMAL))
    return (
        GENERIC_TARGET_CALORIES,
        GENERIC_TARGET_PROTEIN,
        GENERIC_TARGET_FAT,
        target_carb,
    )


def build_recommended_exercises(db: Session, weight_kg: Decimal, goal_type: GoalType) -> list[RecommendedExerciseItem]:
    preferred_category = PREFERRED_EXERCISE_CATEGORY[goal_type]
    exercises = (
        db.query(ExerciseCatalog)
        .filter(ExerciseCatalog.category == preferred_category)
        .order_by(ExerciseCatalog.is_popular.desc(), ExerciseCatalog.display_order.asc())
        .limit(3)
        .all()
    )

    if len(exercises) < 3:
        fallback_ids = {exercise.id for exercise in exercises}
        fallback_exercises = (
            db.query(ExerciseCatalog)
            .filter(~ExerciseCatalog.id.in_(fallback_ids) if fallback_ids else True)
            .order_by(ExerciseCatalog.is_popular.desc(), ExerciseCatalog.display_order.asc())
            .limit(3 - len(exercises))
            .all()
        )
        exercises.extend(fallback_exercises)

    recommendations: list[RecommendedExerciseItem] = []
    for exercise, duration_minutes in zip(exercises, EXERCISE_DURATIONS, strict=False):
        duration_hours = Decimal(duration_minutes) / Decimal("60")
        burn_estimate_kcal = quantize_decimal(exercise.met_value * weight_kg * duration_hours)
        recommendations.append(
            RecommendedExerciseItem(
                exercise_id=exercise.id,
                name=exercise.name,
                category=exercise.category,
                duration_minutes=duration_minutes,
                burn_estimate_kcal=burn_estimate_kcal,
            )
        )

    return recommendations


def build_generic_exercises(db: Session) -> list[RecommendedExerciseItem]:
    exercises = (
        db.query(ExerciseCatalog)
        .order_by(ExerciseCatalog.is_popular.desc(), ExerciseCatalog.display_order.asc())
        .limit(3)
        .all()
    )

    recommendations: list[RecommendedExerciseItem] = []
    for index, exercise in enumerate(exercises):
        recommendations.append(
            RecommendedExerciseItem(
                exercise_id=exercise.id,
                name=exercise.name,
                category=exercise.category,
                duration_minutes=EXERCISE_DURATIONS[index],
                burn_estimate_kcal=GENERIC_EXERCISE_BURN_ESTIMATES[index],
            )
        )

    return recommendations


def build_confirm_response(analysis, recommended_exercises: list[RecommendedExerciseItem]) -> AnalysisConfirmResponse:
    recommendation = build_recommendation_response(analysis.recommendation_snapshot)
    recommendation.recommended_exercises = recommended_exercises

    return AnalysisConfirmResponse(
        analysis_id=analysis.id,
        analyzed_at=analysis.analyzed_at,
        status=analysis.status,
        total_kcal=analysis.total_kcal or ZERO_DECIMAL,
        total_protein_g=analysis.total_protein_g or ZERO_DECIMAL,
        total_fat_g=analysis.total_fat_g or ZERO_DECIMAL,
        total_carb_g=analysis.total_carb_g or ZERO_DECIMAL,
        items=build_analysis_result_items(analysis.items),
        recommendation=recommendation,
        disclaimer=build_non_medical_disclaimer(),
    )


def confirm_analysis(
    db: Session,
    user: User,
    analysis_id: str,
    payload: AnalysisConfirmRequest,
) -> AnalysisConfirmResponse:
    analysis = get_analysis_for_user(db, user, analysis_id)

    if analysis.status != AnalysisStatus.AWAITING_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis confirmation is only allowed after candidate selection",
        )

    profile = get_or_create_profile(db, user)
    analysis.items.clear()

    total_kcal = ZERO_DECIMAL
    total_protein_g = ZERO_DECIMAL
    total_fat_g = ZERO_DECIMAL
    total_carb_g = ZERO_DECIMAL

    for item_payload in payload.items:
        item = build_analysis_item(item_payload)
        analysis.items.append(item)
        total_kcal += item.kcal
        total_protein_g += item.protein_g
        total_fat_g += item.fat_g
        total_carb_g += item.carb_g

    if has_complete_recommendation_profile(profile):
        recommendation_source = PERSONALIZED_RECOMMENDATION_SOURCE
        target_calories, target_protein, target_fat, target_carb = calculate_targets(
            profile.weight_kg,
            profile.activity_level.value,
            profile.goal_type,
        )
        recommended_exercises = build_recommended_exercises(db, profile.weight_kg, profile.goal_type)
    else:
        recommendation_source = GENERIC_RECOMMENDATION_SOURCE
        target_calories, target_protein, target_fat, target_carb = build_generic_targets()
        recommended_exercises = build_generic_exercises(db)

    if analysis.recommendation_snapshot is not None:
        db.delete(analysis.recommendation_snapshot)
        db.flush()

    analysis.total_kcal = quantize_decimal(total_kcal)
    analysis.total_protein_g = quantize_decimal(total_protein_g)
    analysis.total_fat_g = quantize_decimal(total_fat_g)
    analysis.total_carb_g = quantize_decimal(total_carb_g)
    analysis.status = AnalysisStatus.COMPLETED
    analysis.recommendation_snapshot = RecommendationSnapshot(
        source=recommendation_source,
        target_calories_kcal=target_calories,
        target_protein_g=target_protein,
        target_fat_g=target_fat,
        target_carb_g=target_carb,
        recommended_exercises_json=[json.loads(item.model_dump_json()) for item in recommended_exercises],
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    delete_analysis_uploads(analysis.id)
    return build_confirm_response(analysis, recommended_exercises)
