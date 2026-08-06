"""Meal repository — raw DB access for the Meal table only."""

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.meal import Meal


class MealRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, meal: Meal) -> Meal:
        self.db.add(meal)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def get_by_id(self, meal_id: int) -> Meal | None:
        return self.db.get(Meal, meal_id)

    def list_by_user(self, user_id: int, limit: int = 50) -> list[Meal]:
        """
        Ordered by (meal_time DESC, id DESC) for the same reason as
        conversation history: meal_time alone can tie at 1-second DATETIME
        resolution if two meals are logged in quick succession, so id
        (strictly increasing with insertion order) breaks the tie.
        """
        return (
            self.db.query(Meal)
            .filter(Meal.user_id == user_id)
            .order_by(desc(Meal.meal_time), desc(Meal.id))
            .limit(limit)
            .all()
        )
