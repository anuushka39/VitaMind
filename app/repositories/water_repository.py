from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.water import WaterLog
from app.repositories.base import BaseRepository


class WaterLogRepository(BaseRepository[WaterLog]):
    model = WaterLog

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[WaterLog]:
        stmt = (
            select(WaterLog)
            .where(WaterLog.user_id == user_id)
            .order_by(WaterLog.logged_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_user_on_date(self, user_id: int, day: date) -> list[WaterLog]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        stmt = (
            select(WaterLog)
            .where(WaterLog.user_id == user_id, WaterLog.logged_at.between(start, end))
            .order_by(WaterLog.logged_at)
        )
        return list(self.db.scalars(stmt).all())
