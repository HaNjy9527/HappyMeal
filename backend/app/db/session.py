from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


@lru_cache
def get_engine():
    return create_engine(settings.normalized_database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory():
    return sessionmaker(autoflush=False, autocommit=False, class_=Session)


def can_connect_to_database() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False

    return True


def get_db():
    database_session = get_session_factory()(bind=get_engine())

    try:
        yield database_session
    finally:
        database_session.close()
