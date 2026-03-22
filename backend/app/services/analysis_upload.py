from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AnalysisStatus, FoodAnalysis, User
from app.schemas.analysis import AnalysisCandidateItem, AnalysisCandidateResponse


MOCK_CANDIDATE_PRESETS = {
    "salad": [
        AnalysisCandidateItem(
            food_name="Chicken Salad",
            normalized_food_name="chicken_salad",
            confidence_score=Decimal("0.942"),
            portion_default=Decimal("1.00"),
            portion_unit="bowl",
        ),
        AnalysisCandidateItem(
            food_name="Boiled Egg",
            normalized_food_name="boiled_egg",
            confidence_score=Decimal("0.811"),
            portion_default=Decimal("1.00"),
            portion_unit="pcs",
        ),
    ],
    "rice": [
        AnalysisCandidateItem(
            food_name="Grilled Chicken Rice",
            normalized_food_name="grilled_chicken_rice",
            confidence_score=Decimal("0.918"),
            portion_default=Decimal("1.00"),
            portion_unit="plate",
        ),
        AnalysisCandidateItem(
            food_name="Stir-fried Vegetables",
            normalized_food_name="stir_fried_vegetables",
            confidence_score=Decimal("0.768"),
            portion_default=Decimal("0.50"),
            portion_unit="plate",
        ),
    ],
}

DEFAULT_MOCK_CANDIDATES = [
    AnalysisCandidateItem(
        food_name="Grilled Salmon",
        normalized_food_name="grilled_salmon",
        confidence_score=Decimal("0.903"),
        portion_default=Decimal("1.00"),
        portion_unit="fillet",
    ),
    AnalysisCandidateItem(
        food_name="Brown Rice",
        normalized_food_name="brown_rice",
        confidence_score=Decimal("0.845"),
        portion_default=Decimal("1.00"),
        portion_unit="bowl",
    ),
    AnalysisCandidateItem(
        food_name="Steamed Broccoli",
        normalized_food_name="steamed_broccoli",
        confidence_score=Decimal("0.732"),
        portion_default=Decimal("0.50"),
        portion_unit="bowl",
    ),
]


def get_analysis_for_user(db: Session, user: User, analysis_id: str) -> FoodAnalysis:
    analysis = (
        db.query(FoodAnalysis)
        .filter(FoodAnalysis.id == analysis_id, FoodAnalysis.user_id == user.id)
        .one_or_none()
    )

    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return analysis


def validate_image_upload(file: UploadFile) -> None:
    allowed_content_types = {"image/jpeg", "image/png"}

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG images are supported",
        )


def build_upload_path(analysis_id: str, filename: str | None) -> Path:
    settings = get_settings()
    suffix = ".jpg"

    if filename:
        filename_suffix = Path(filename).suffix.lower()
        if filename_suffix in {".jpg", ".jpeg", ".png"}:
            suffix = filename_suffix

    settings.analysis_upload_path.mkdir(parents=True, exist_ok=True)
    return settings.analysis_upload_path / f"{analysis_id}{suffix}"


def save_upload_file(file: UploadFile, target_path: Path) -> None:
    settings = get_settings()
    content = file.file.read()

    if len(content) > settings.analysis_max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image exceeds the 5MB upload limit",
        )

    target_path.write_bytes(content)


def build_mock_candidates(filename: str | None) -> list[AnalysisCandidateItem]:
    if filename:
        normalized_filename = filename.lower()

        if "salad" in normalized_filename:
            return MOCK_CANDIDATE_PRESETS["salad"]

        if "rice" in normalized_filename:
            return MOCK_CANDIDATE_PRESETS["rice"]

    return DEFAULT_MOCK_CANDIDATES


def upload_analysis_image(
    db: Session,
    user: User,
    analysis_id: str,
    file: UploadFile,
) -> AnalysisCandidateResponse:
    analysis = get_analysis_for_user(db, user, analysis_id)

    if analysis.status != AnalysisStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image upload is only allowed for draft analyses",
        )

    validate_image_upload(file)
    target_path = build_upload_path(analysis_id, file.filename)
    save_upload_file(file, target_path)

    analysis.status = AnalysisStatus.AWAITING_CONFIRMATION
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return AnalysisCandidateResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        candidates=build_mock_candidates(file.filename),
    )
