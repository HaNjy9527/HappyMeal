import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db


logger = logging.getLogger("app.auth")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        logger.warning(
            "Authentication required but no session user_id found",
            extra={
                "event": "auth_me_unauthenticated",
                "endpoint": "auth.me",
                "outcome": "unauthenticated",
                "reason": "missing_session_user_id",
                "status_code": status.HTTP_401_UNAUTHORIZED,
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
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user