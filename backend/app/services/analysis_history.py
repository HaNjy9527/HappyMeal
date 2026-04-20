from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db.models import AnalysisStatus, FoodAnalysis, User
from app.schemas.analysis import AnalysisHistoryDetailResponse, AnalysisHistoryListItem, AnalysisHistoryListResponse
from app.services.analysis import get_analysis_for_user
from app.services.analysis_views import build_analysis_detail_response, build_food_summary, build_recommendation_summary
from app.services.consent import build_non_medical_disclaimer


ZERO_DECIMAL = Decimal("0.00")


def list_completed_analyses(db: Session, user: User) -> AnalysisHistoryListResponse:
    analyses = (
        db.query(FoodAnalysis)
        .options(joinedload(FoodAnalysis.items), joinedload(FoodAnalysis.recommendation_snapshot))
        .filter(FoodAnalysis.user_id == user.id, FoodAnalysis.status == AnalysisStatus.COMPLETED)
        .order_by(FoodAnalysis.analyzed_at.desc())
        .all()
    )

    return AnalysisHistoryListResponse(
        items=[
            AnalysisHistoryListItem(
                analysis_id=analysis.id,
                analyzed_at=analysis.analyzed_at,
                total_kcal=analysis.total_kcal or ZERO_DECIMAL,
                food_summary=build_food_summary(analysis.items),
                recommendation_summary=build_recommendation_summary(analysis.recommendation_snapshot),
            )
            for analysis in analyses
        ]
    )


def get_completed_analysis_detail(db: Session, user: User, analysis_id: str) -> AnalysisHistoryDetailResponse:
    analysis = get_analysis_for_user(db, user, analysis_id)

    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="History detail is only available for completed analyses")

    hydrated_analysis = (
        db.query(FoodAnalysis)
        .options(joinedload(FoodAnalysis.items), joinedload(FoodAnalysis.recommendation_snapshot))
        .filter(FoodAnalysis.id == analysis.id, FoodAnalysis.user_id == user.id)
        .one()
    )
    return build_analysis_detail_response(hydrated_analysis, build_non_medical_disclaimer())