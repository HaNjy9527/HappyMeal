from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest, ThemePreferenceUpdateRequest
from app.services.profile import build_profile_response, update_profile, update_theme_preference


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProfileResponse:
    return build_profile_response(db, user)


@router.put("", response_model=ProfileResponse)
def put_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    return update_profile(db, user, payload)


@router.put("/theme", response_model=ProfileResponse)
def put_theme_preference(
    payload: ThemePreferenceUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    return update_theme_preference(db, user, payload)