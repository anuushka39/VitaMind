"""Meal log entries."""

from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Meal(Base, TimestampMixin):
    __tablename__ = "meals"
    __table_args__ = (
        Index("ix_meals_user_logged_at", "user_id", "logged_at"),
        CheckConstraint("calories IS NULL OR calories >= 0", name="ck_meals_calories_nonneg"),
        CheckConstraint("protein_g IS NULL OR protein_g >= 0", name="ck_meals_protein_nonneg"),
        CheckConstraint("carbs_g IS NULL OR carbs_g >= 0", name="ck_meals_carbs_nonneg"),
        CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_meals_fat_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)  # breakfast|lunch|dinner|snack
    items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    calories: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="meals")
