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
)
from app.services.analysis import create_analysis_draft
from app.services.analysis_confirm import confirm_analysis
from app.services.analysis_upload import upload_analysis_image


router = APIRouter(prefix="/analyses", tags=["analyses"])


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
