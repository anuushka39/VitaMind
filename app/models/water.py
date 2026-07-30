"""Water intake log entries."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class WaterLog(Base, TimestampMixin):
    __tablename__ = "water_logs"
    __table_args__ = (
        Index("ix_water_user_logged_at", "user_id", "logged_at"),
        CheckConstraint("amount_ml > 0", name="ck_water_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="water_logs")
