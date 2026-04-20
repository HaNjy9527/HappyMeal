import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.core.config import get_settings


logger = logging.getLogger("app.auth")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    cookie_header_present = request.headers.get("cookie") is not None
    session_cookie_present = settings.session_cookie_name in request.cookies
    user_id = request.session.get("user_id")
    if not user_id:
        event_name = (
            "auth_me_cookie_present_but_session_missing"
            if session_cookie_present
            else "auth_me_cookie_missing"
        )
        logger.warning(
            "Authentication required but no session user_id found",
            extra={
                "event": event_name,
                "endpoint": "auth.me",
                "outcome": "unauthenticated",
                "reason": "missing_session_user_id",
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "cookie_header_present": cookie_header_present,
                "session_cookie_present": session_cookie_present,
                "session_contains_user_id": False,
                "session_cookie_name": settings.session_cookie_name,
                "session_key_count": len(request.session),
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        request.session.clear()
        logger.warning(
            "Authenticated session referenced missing user",
            extra={
                "event": "auth_me_user_missing",
                "endpoint": "auth.me",
                "outcome": "unauthenticated",
                "reason": "session_user_not_found",
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "user_id": user_id,
                "cookie_header_present": cookie_header_present,
                "session_cookie_present": session_cookie_present,
                "session_contains_user_id": True,
                "session_cookie_name": settings.session_cookie_name,
                "session_key_count": len(request.session),
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user