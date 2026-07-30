"""User dietary/fitness preferences — one-to-one with User."""

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Preferences(Base, TimestampMixin):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    diet_type: Mapped[str] = mapped_column(String(20), default="non_vegetarian")  # vegetarian | non_vegetarian | vegan
    allergies: Mapped[list | None] = mapped_column(JSON, default=list)
    disliked_foods: Mapped[list | None] = mapped_column(JSON, default=list)
    fitness_goal: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="preferences")
