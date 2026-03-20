from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.db import models  # noqa: F401,E402
