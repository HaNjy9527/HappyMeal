from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import User


LINE_AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"
LINE_SCOPE = "profile openid"
LINE_STATE_MAX_AGE_SECONDS = 60 * 10
AUTH_TOKEN_MAX_AGE_SECONDS = 60 * 2  # 2-minute window for mobile browser handoff


def build_auth_token_signer(settings: Settings) -> TimestampSigner:
    secret_key = settings.session_secret_key or "dev-session-secret"
    return TimestampSigner(secret_key, salt="line-auth-token")


def create_auth_token(user_id: str, settings: Settings) -> str:
    signer = build_auth_token_signer(settings)
    return signer.sign(user_id).decode("utf-8")


def verify_auth_token(token: str, settings: Settings) -> str:
    signer = build_auth_token_signer(settings)
    try:
        user_id = signer.unsign(token, max_age=AUTH_TOKEN_MAX_AGE_SECONDS)
        return user_id.decode("utf-8")
    except SignatureExpired as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auth token expired") from exc
    except BadSignature as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid auth token") from exc


def build_state_signer(settings: Settings) -> TimestampSigner:
    secret_key = settings.session_secret_key or "dev-session-secret"
    return TimestampSigner(secret_key, salt="line-oauth-state")


def create_oauth_state(settings: Settings) -> str:
    raw_state = secrets.token_urlsafe(32)
    signer = build_state_signer(settings)
    return signer.sign(raw_state).decode("utf-8")


def build_line_login_url(settings: Settings, state: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.line_channel_id,
            "redirect_uri": settings.line_callback_url,
            "state": state,
            "scope": LINE_SCOPE,
        }
    )
    return f"{LINE_AUTH_URL}?{query}"


def validate_oauth_state(settings: Settings, expected_state: str | None, actual_state: str | None) -> None:
    if not actual_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter")

    if expected_state and expected_state == actual_state:
        return

    signer = build_state_signer(settings)

    try:
        signer.unsign(actual_state, max_age=LINE_STATE_MAX_AGE_SECONDS)
    except SignatureExpired as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter") from exc
    except BadSignature as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state parameter") from exc


def exchange_code_for_access_token(settings: Settings, code: str | None) -> str:
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    try:
        response = httpx.post(
            LINE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.line_callback_url,
                "client_id": settings.line_channel_id,
                "client_secret": settings.line_channel_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to exchange token") from exc

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange token")

    access_token = response.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing access token")

    return access_token


def fetch_line_profile(access_token: str) -> dict[str, str | None]:
    try:
        response = httpx.get(
            LINE_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to get LINE profile") from exc

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get LINE profile")

    payload = response.json()
    line_user_id = payload.get("userId")
    if not line_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing LINE user id")

    return {
        "line_user_id": line_user_id,
        "display_name": payload.get("displayName", ""),
        "avatar_url": payload.get("pictureUrl"),
    }


def upsert_line_user(db: Session, profile: dict[str, str | None]) -> User:
    user = db.query(User).filter(User.line_user_id == profile["line_user_id"]).one_or_none()

    if user is None:
        user = User(
            line_user_id=str(profile["line_user_id"]),
            display_name=str(profile["display_name"] or ""),
            avatar_url=profile["avatar_url"],
        )
        db.add(user)
    else:
        user.display_name = str(profile["display_name"] or "")
        user.avatar_url = profile["avatar_url"]

    db.commit()
    db.refresh(user)
    return user


def build_frontend_redirect_url(
    frontend_url: str,
    path: str,
    error: str | None = None,
    token: str | None = None,
) -> str:
    from urllib.parse import urlencode

    base_url = frontend_url.rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"

    params: dict[str, str] = {}
    if error:
        params["error"] = error
    if token:
        params["token"] = token

    if params:
        return f"{base_url}{normalized_path}?{urlencode(params)}"

    return f"{base_url}{normalized_path}"