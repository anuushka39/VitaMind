from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.weight import WeightLog
from app.repositories.base import BaseRepository


class WeightLogRepository(BaseRepository[WeightLog]):
    model = WeightLog

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[WeightLog]:
        stmt = (
            select(WeightLog)
            .where(WeightLog.user_id == user_id)
            .order_by(WeightLog.logged_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_user_on_date(self, user_id: int, day: date) -> list[WeightLog]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        stmt = (
            select(WeightLog)
            .where(WeightLog.user_id == user_id, WeightLog.logged_at.between(start, end))
            .order_by(WeightLog.logged_at)
        )
        return list(self.db.scalars(stmt).all())
