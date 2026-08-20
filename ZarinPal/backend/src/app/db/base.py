from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import model modules here so Alembic discovers their metadata.
from app.models import transactions  # noqa: E402, F401
