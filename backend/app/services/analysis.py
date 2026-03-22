from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import FoodAnalysis, User


def create_analysis_draft(db: Session, user: User) -> FoodAnalysis:
    analysis = FoodAnalysis(user_id=user.id)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis_for_user(db: Session, user: User, analysis_id: str) -> FoodAnalysis:
    analysis = (
        db.query(FoodAnalysis)
        .filter(FoodAnalysis.id == analysis_id, FoodAnalysis.user_id == user.id)
        .one_or_none()
    )

    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return analysis
