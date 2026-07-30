"""User goals (weight target, fitness target, etc.)."""

from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"
    __table_args__ = (
        Index("ix_goals_user_id", "user_id"),
        CheckConstraint("target_value IS NULL OR target_value > 0", name="ck_goals_target_positive"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_goals_end_after_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(30), nullable=False)  # weight_loss|weight_gain|muscle_gain|maintenance
    target_value: Mapped[float | None] = mapped_column(Float)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="goals")
