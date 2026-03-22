from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import AnalysisStatus


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