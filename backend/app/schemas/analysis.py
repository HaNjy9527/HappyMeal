from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import AnalysisStatus, ConsentType


class AnalysisDraftResponse(BaseModel):
    id: str
    analyzed_at: datetime
    status: AnalysisStatus

    model_config = ConfigDict(from_attributes=True)


class AnalysisCandidateItem(BaseModel):
    food_name: str
    normalized_food_name: str
    confidence_score: Decimal = Field(ge=0, le=1)
    portion_default: Decimal = Field(gt=0)
    portion_unit: str


class AnalysisCandidateResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    candidates: list[AnalysisCandidateItem]


class AnalysisConfirmItemRequest(BaseModel):
    food_name: str
    normalized_food_name: str
    portion_value: Decimal = Field(gt=0)
    portion_unit: str
    confidence_score: Decimal | None = Field(default=None, ge=0, le=1)


class AnalysisConfirmRequest(BaseModel):
    items: list[AnalysisConfirmItemRequest] = Field(min_length=1)


class AnalysisResultItem(BaseModel):
    food_name: str
    normalized_food_name: str
    portion_value: Decimal
    portion_unit: str
    source_portion_unit: str | None = None
    canonical_food_name: str | None = None
    nutrition_source: str | None = None
    is_estimated: bool = False
    resolved_weight_g: Decimal | None = None
    weight_estimation_method: str | None = None
    confidence_score: Decimal | None
    kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carb_g: Decimal


class RecommendedExerciseItem(BaseModel):
    exercise_id: str
    name: str
    category: str
    duration_minutes: int
    burn_estimate_kcal: Decimal


class RecommendationSnapshotResponse(BaseModel):
    target_calories_kcal: Decimal
    target_protein_g: Decimal
    target_fat_g: Decimal
    target_carb_g: Decimal
    recommended_exercises: list[RecommendedExerciseItem]


class DisclaimerResponse(BaseModel):
    title: str
    body: str
    policy_version: str
    consent_type: ConsentType


class AnalysisConfirmResponse(BaseModel):
    analysis_id: str
    analyzed_at: datetime
    status: AnalysisStatus
    total_kcal: Decimal
    total_protein_g: Decimal
    total_fat_g: Decimal
    total_carb_g: Decimal
    items: list[AnalysisResultItem]
    recommendation: RecommendationSnapshotResponse
    disclaimer: DisclaimerResponse


class AnalysisHistoryListItem(BaseModel):
    analysis_id: str
    analyzed_at: datetime
    total_kcal: Decimal
    food_summary: str
    recommendation_summary: str


class AnalysisHistoryListResponse(BaseModel):
    items: list[AnalysisHistoryListItem]


class AnalysisHistoryDetailResponse(BaseModel):
    analysis_id: str
    analyzed_at: datetime
    status: AnalysisStatus
    food_summary: str
    total_kcal: Decimal
    total_protein_g: Decimal
    total_fat_g: Decimal
    total_carb_g: Decimal
    items: list[AnalysisResultItem]
    recommendation: RecommendationSnapshotResponse
    disclaimer: DisclaimerResponse