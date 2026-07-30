"""User model — the root entity every other table hangs off of."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    telegram_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    whatsapp_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)

    preferences: Mapped["Preferences | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    meals: Mapped[list["Meal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    exercise_logs: Mapped[list["ExerciseLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    water_logs: Mapped[list["WaterLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sleep_logs: Mapped[list["SleepLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    weight_logs: Mapped[list["WeightLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
