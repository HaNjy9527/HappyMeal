from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db


def get_current_user(db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    user = db.query(User).filter(User.line_user_id == settings.mock_line_user_id).one_or_none()

    if user is not None:
        return user

    user = User(
        line_user_id=settings.mock_line_user_id,
        display_name=settings.mock_display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user