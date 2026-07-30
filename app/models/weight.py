"""Weight log entries."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class WeightLog(Base, TimestampMixin):
    __tablename__ = "weight_logs"
    __table_args__ = (
        Index("ix_weight_user_logged_at", "user_id", "logged_at"),
        CheckConstraint("weight_kg > 0", name="ck_weight_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="weight_logs")
