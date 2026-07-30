from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.meal import Meal
from app.repositories.base import BaseRepository


class MealRepository(BaseRepository[Meal]):
    model = Meal

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Meal]:
        stmt = (
            select(Meal)
            .where(Meal.user_id == user_id)
            .order_by(Meal.logged_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_user_on_date(self, user_id: int, day: date) -> list[Meal]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        stmt = (
            select(Meal)
            .where(Meal.user_id == user_id, Meal.logged_at.between(start, end))
            .order_by(Meal.logged_at)
        )
        return list(self.db.scalars(stmt).all())
