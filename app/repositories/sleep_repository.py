from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sleep import SleepLog
from app.repositories.base import BaseRepository


class SleepLogRepository(BaseRepository[SleepLog]):
    model = SleepLog

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[SleepLog]:
        stmt = (
            select(SleepLog)
            .where(SleepLog.user_id == user_id)
            .order_by(SleepLog.logged_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_user_on_date(self, user_id: int, day: date) -> list[SleepLog]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        stmt = (
            select(SleepLog)
            .where(SleepLog.user_id == user_id, SleepLog.logged_at.between(start, end))
            .order_by(SleepLog.logged_at)
        )
        return list(self.db.scalars(stmt).all())
