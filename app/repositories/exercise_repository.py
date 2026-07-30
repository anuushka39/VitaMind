from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exercise import ExerciseLog
from app.repositories.base import BaseRepository


class ExerciseLogRepository(BaseRepository[ExerciseLog]):
    model = ExerciseLog

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[ExerciseLog]:
        stmt = (
            select(ExerciseLog)
            .where(ExerciseLog.user_id == user_id)
            .order_by(ExerciseLog.logged_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_user_on_date(self, user_id: int, day: date) -> list[ExerciseLog]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        stmt = (
            select(ExerciseLog)
            .where(ExerciseLog.user_id == user_id, ExerciseLog.logged_at.between(start, end))
            .order_by(ExerciseLog.logged_at)
        )
        return list(self.db.scalars(stmt).all())
