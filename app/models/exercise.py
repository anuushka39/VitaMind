"""Exercise log entries."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class ExerciseLog(Base, TimestampMixin):
    __tablename__ = "exercise_logs"
    __table_args__ = (
        Index("ix_exercise_user_logged_at", "user_id", "logged_at"),
        CheckConstraint("duration_min > 0", name="ck_exercise_duration_positive"),
        CheckConstraint("calories_burned IS NULL OR calories_burned >= 0", name="ck_exercise_calories_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    calories_burned: Mapped[float | None] = mapped_column(Float)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="exercise_logs")
