from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import AuthMeResponse
from app.services.auth import (
    build_frontend_redirect_url,
    build_line_login_url,
    create_auth_token,
    create_oauth_state,
    exchange_code_for_access_token,
    fetch_line_profile,
    upsert_line_user,
    validate_oauth_state,
    verify_auth_token,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class ExchangeTokenRequest(BaseModel):
    token: str


@router.get("/line/login")
def get_line_login(request: Request) -> RedirectResponse:
    settings = get_settings()
    state = create_oauth_state(settings)
    request.session["oauth_state"] = state
    return RedirectResponse(url=build_line_login_url(settings, state), status_code=302)


@router.get("/line/callback")
def get_line_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()

    if error:
        return RedirectResponse(
            url=build_frontend_redirect_url(settings.frontend_url, "/", error="line_auth_denied"),
            status_code=302,
        )

    validate_oauth_state(settings, request.session.pop("oauth_state", None), state)
    access_token = exchange_code_for_access_token(settings, code)
    profile = fetch_line_profile(access_token)
    user = upsert_line_user(db, profile)

    auth_token = create_auth_token(user.id, settings)
    return RedirectResponse(
        url=build_frontend_redirect_url(settings.frontend_url, "/", token=auth_token),
        status_code=302,
    )


@router.post("/exchange-token", response_model=AuthMeResponse)
def post_exchange_token(
    request: Request,
    body: ExchangeTokenRequest,
    db: Session = Depends(get_db),
) -> AuthMeResponse:
    settings = get_settings()
    user_id = verify_auth_token(body.token, settings)
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    request.session["user_id"] = user.id
    return AuthMeResponse.model_validate(user)


@router.get("/me", response_model=AuthMeResponse)
def get_me(user: User = Depends(get_current_user)) -> AuthMeResponse:
    return AuthMeResponse.model_validate(user)


@router.post("/logout")
def post_logout(request: Request) -> dict[str, str]:
    request.session.clear()
    return {"message": "Logged out"}