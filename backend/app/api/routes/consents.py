from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.consent import ConsentCreateRequest, ConsentRecordResponse, CurrentConsentsResponse
from app.services.consent import create_consent, list_current_consents


router = APIRouter(prefix="/consents", tags=["consents"])


@router.get("/current", response_model=CurrentConsentsResponse)
def get_current_consents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CurrentConsentsResponse:
    items = list_current_consents(db, user)
    return CurrentConsentsResponse(items=[ConsentRecordResponse.model_validate(item) for item in items])


@router.post("", response_model=ConsentRecordResponse, status_code=status.HTTP_201_CREATED)
def post_consent(
    payload: ConsentCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConsentRecordResponse:
    consent = create_consent(db, user, payload)
    return ConsentRecordResponse.model_validate(consent)