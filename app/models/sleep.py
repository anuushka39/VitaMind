"""Sleep log entries."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class SleepLog(Base, TimestampMixin):
    __tablename__ = "sleep_logs"
    __table_args__ = (
        Index("ix_sleep_user_logged_at", "user_id", "logged_at"),
        CheckConstraint("hours > 0 AND hours <= 24", name="ck_sleep_hours_valid_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    hours: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[str | None] = mapped_column(String(20))  # poor|average|good
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sleep_logs")
