import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import AuthMeResponse
from app.services.consent import build_consent_status, build_required_policy_versions
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
logger = logging.getLogger("app.auth")


def build_auth_me_response(db: Session, user: User) -> AuthMeResponse:
    return AuthMeResponse(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        theme_preference=user.theme_preference,
        consent_status=build_consent_status(db, user),
        required_policy_versions=build_required_policy_versions(),
    )


def build_cookie_debug_context(settings, request: Request) -> dict[str, object]:
    return {
        "session_cookie_name": settings.session_cookie_name,
        "session_cookie_domain": settings.session_cookie_domain,
        "same_site_policy": settings.effective_session_cookie_same_site,
        "https_only": settings.effective_session_cookie_https_only,
        "is_production": settings.is_production,
        "session_cookie_max_age": settings.session_cookie_max_age,
        "allow_credentials": True,
        "cookie_header_present": request.headers.get("cookie") is not None,
        "session_cookie_present": settings.session_cookie_name in request.cookies,
        "session_contains_user_id": "user_id" in request.session,
        "session_key_count": len(request.session),
    }


class ExchangeTokenRequest(BaseModel):
    token: str


@router.get("/line/login")
def get_line_login(request: Request) -> RedirectResponse:
    settings = get_settings()
    logger.info(
        "LINE login flow started",
        extra={
            "event": "line_login_started",
            "endpoint": "auth.line_login",
            "outcome": "started",
        },
    )
    state = create_oauth_state(settings)
    request.session["oauth_state"] = state
    logger.info(
        "Redirecting to LINE authorize URL",
        extra={
            "event": "line_login_redirected",
            "endpoint": "auth.line_login",
            "outcome": "redirect",
            "redirect_target": "line_authorize_url",
        },
    )
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
    logger.info(
        "Received LINE callback request",
        extra={
            "event": "line_callback_received",
            "endpoint": "auth.line_callback",
            "outcome": "received",
            "has_code": code is not None,
            "has_state": state is not None,
            "has_error": error is not None,
        },
    )

    if error:
        logger.warning(
            "LINE callback returned an authorization error",
            extra={
                "event": "line_callback_denied",
                "endpoint": "auth.line_callback",
                "outcome": "failure",
                "reason": error,
                "status_code": status.HTTP_302_FOUND,
                "redirect_target": "frontend_root_with_error",
            },
        )
        return RedirectResponse(
            url=build_frontend_redirect_url(settings.frontend_url, "/", error="line_auth_denied"),
            status_code=302,
        )

    validate_oauth_state(settings, request.session.pop("oauth_state", None), state)
    access_token = exchange_code_for_access_token(settings, code)
    profile = fetch_line_profile(access_token)
    user = upsert_line_user(db, profile)

    auth_token = create_auth_token(user.id, settings)
    logger.info(
        "Redirecting frontend to exchange signed auth token",
        extra={
            "event": "line_callback_redirected",
            "endpoint": "auth.line_callback",
            "outcome": "redirect",
            "user_id": user.id,
            "redirect_target": "frontend_root_with_auth_token",
        },
    )
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
    logger.info(
        "Received auth token exchange request",
        extra={
            "event": "exchange_token_requested",
            "endpoint": "auth.exchange_token",
            "outcome": "started",
            **build_cookie_debug_context(settings, request),
        },
    )
    user_id = verify_auth_token(body.token, settings)
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        logger.warning(
            "Auth token exchange referenced a missing user",
            extra={
                "event": "exchange_token_user_missing",
                "endpoint": "auth.exchange_token",
                "outcome": "failure",
                "reason": "user_not_found",
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "user_id": user_id,
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    request.session["user_id"] = user.id
    logger.info(
        "Established session from exchanged auth token",
        extra={
            "event": "session_established",
            "endpoint": "auth.exchange_token",
            "outcome": "success",
            "user_id": user.id,
            **build_cookie_debug_context(settings, request),
        },
    )
    logger.info(
        "Prepared response to write session cookie",
        extra={
            "event": "session_cookie_write_attempted",
            "endpoint": "auth.exchange_token",
            "outcome": "success",
            "user_id": user.id,
            "response_will_set_cookie": True,
            **build_cookie_debug_context(settings, request),
        },
    )
    return build_auth_me_response(db, user)


@router.get("/me", response_model=AuthMeResponse)
def get_me(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AuthMeResponse:
    settings = get_settings()
    logger.info(
        "Resolved authenticated user profile",
        extra={
            "event": "auth_me_succeeded",
            "endpoint": "auth.me",
            "outcome": "success",
            "user_id": user.id,
            **build_cookie_debug_context(settings, request),
        },
    )
    return build_auth_me_response(db, user)


@router.post("/logout")
def post_logout(request: Request) -> dict[str, str]:
    user_id = request.session.get("user_id")
    request.session.clear()
    logger.info(
        "Cleared authenticated session",
        extra={
            "event": "logout_completed",
            "endpoint": "auth.logout",
            "outcome": "success",
            "user_id": user_id,
        },
    )
    return {"message": "Logged out"}