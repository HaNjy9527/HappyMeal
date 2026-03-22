from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisCandidateResponse,
    AnalysisConfirmRequest,
    AnalysisConfirmResponse,
    AnalysisDraftResponse,
    AnalysisHistoryDetailResponse,
    AnalysisHistoryListResponse,
)
from app.services.analysis import create_analysis_draft
from app.services.analysis_confirm import confirm_analysis
from app.services.analysis_history import get_completed_analysis_detail, list_completed_analyses
from app.services.analysis_upload import upload_analysis_image


router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.get("", response_model=AnalysisHistoryListResponse)
def get_analysis_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisHistoryListResponse:
    return list_completed_analyses(db, user)


@router.post("", response_model=AnalysisDraftResponse, status_code=status.HTTP_201_CREATED)
def post_analysis_draft(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisDraftResponse:
    analysis = create_analysis_draft(db, user)
    return AnalysisDraftResponse.model_validate(analysis)


@router.post("/{analysis_id}/image", response_model=AnalysisCandidateResponse)
def post_analysis_image(
    analysis_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisCandidateResponse:
    return upload_analysis_image(db, user, analysis_id, file)


@router.post("/{analysis_id}/confirm", response_model=AnalysisConfirmResponse)
def post_analysis_confirm(
    analysis_id: str,
    payload: AnalysisConfirmRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisConfirmResponse:
    return confirm_analysis(db, user, analysis_id, payload)


@router.get("/{analysis_id}", response_model=AnalysisHistoryDetailResponse)
def get_analysis_detail(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisHistoryDetailResponse:
    return get_completed_analysis_detail(db, user, analysis_id)
