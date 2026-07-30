"""
Shared SQLAlchemy declarative base.

Separate from session.py on purpose: session.py owns the *connection*
(engine, sessions); base.py owns the *mapping registry* that every model
attaches to. Alembic's env.py imports Base.metadata to know what tables
should exist — it does not need the engine for that. Keeping these apart
means a model file only ever needs `from app.database.base import Base`,
with zero awareness of how the app connects to the database.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin adding created_at/updated_at to any model that inherits it.
    Lives here (not in a model file) because it's schema-shape, not a table
    of its own — every model in this app uses it."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
