from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status

from app.db.models import FoodAnalysis, FoodAnalysisItem, RecommendationSnapshot
from app.schemas.analysis import (
    AnalysisHistoryDetailResponse,
    AnalysisResultItem,
    DisclaimerResponse,
    RecommendedExerciseItem,
    RecommendationSnapshotResponse,
)


ZERO_DECIMAL = Decimal("0.00")
GENERIC_RECOMMENDATION_NOTE = "這是通用版建議，補完個人資料可得到更貼近你的建議。"
KCAL_ANOMALY_THRESHOLD = Decimal("1500.00")


def _is_item_anomalous(item: FoodAnalysisItem) -> bool:
    return item.is_estimated and item.kcal > KCAL_ANOMALY_THRESHOLD


def build_analysis_result_items(items: list[FoodAnalysisItem]) -> list[AnalysisResultItem]:
    return [
        AnalysisResultItem(
            food_name=item.food_name,
            normalized_food_name=item.normalized_food_name,
            portion_value=item.portion_value,
            portion_unit=item.portion_unit,
            source_portion_unit=item.source_portion_unit,
            canonical_food_name=item.canonical_food_name,
            nutrition_source=item.nutrition_source,
            is_estimated=item.is_estimated,
            resolved_weight_g=item.resolved_weight_g,
            weight_estimation_method=item.weight_estimation_method,
            confidence_score=item.confidence_score,
            kcal=item.kcal,
            protein_g=item.protein_g,
            fat_g=item.fat_g,
            carb_g=item.carb_g,
            is_anomalous=_is_item_anomalous(item),
        )
        for item in items
    ]


def build_recommendation_response(snapshot: RecommendationSnapshot | None) -> RecommendationSnapshotResponse:
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Recommendation snapshot was not created")

    recommended_exercises = [RecommendedExerciseItem.model_validate(item) for item in snapshot.recommended_exercises_json]
    return RecommendationSnapshotResponse(
        source=snapshot.source,
        guidance_note=GENERIC_RECOMMENDATION_NOTE if snapshot.source == "generic" else None,
        target_calories_kcal=snapshot.target_calories_kcal,
        target_protein_g=snapshot.target_protein_g,
        target_fat_g=snapshot.target_fat_g,
        target_carb_g=snapshot.target_carb_g,
        recommended_exercises=recommended_exercises,
    )


def build_food_summary(items: list[FoodAnalysisItem]) -> str:
    food_names = [item.food_name for item in items]
    if not food_names:
        return "No food items"

    summary_names = food_names[:2]
    summary = ", ".join(summary_names)
    if len(food_names) > 2:
        summary = f"{summary} +{len(food_names) - 2} more"

    return summary


def build_recommendation_summary(snapshot: RecommendationSnapshot | None) -> str:
    recommendation = build_recommendation_response(snapshot)
    exercise_names = [item.name for item in recommendation.recommended_exercises[:2]]
    if not exercise_names:
        return "No recommendations"

    summary = ", ".join(exercise_names)
    if len(recommendation.recommended_exercises) > 2:
        summary = f"{summary} +{len(recommendation.recommended_exercises) - 2} more"

    return summary


def build_analysis_detail_response(
    analysis: FoodAnalysis,
    disclaimer: DisclaimerResponse,
) -> AnalysisHistoryDetailResponse:
    return AnalysisHistoryDetailResponse(
        analysis_id=analysis.id,
        analyzed_at=analysis.analyzed_at,
        status=analysis.status,
        food_summary=build_food_summary(analysis.items),
        total_kcal=analysis.total_kcal or ZERO_DECIMAL,
        total_protein_g=analysis.total_protein_g or ZERO_DECIMAL,
        total_fat_g=analysis.total_fat_g or ZERO_DECIMAL,
        total_carb_g=analysis.total_carb_g or ZERO_DECIMAL,
        items=build_analysis_result_items(analysis.items),
        recommendation=build_recommendation_response(analysis.recommendation_snapshot),
        disclaimer=disclaimer,
    )