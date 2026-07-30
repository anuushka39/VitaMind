from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.middleware.error_handlers import NotFoundError
from app.models.meal import Meal
from app.repositories.meal_repository import MealRepository
from app.repositories.user_repository import UserRepository
from app.schemas.meal import MealCreate, MealUpdate


class MealService:
    def __init__(self, db: Session):
        self.repo = MealRepository(db)
        self.user_repo = UserRepository(db)

    def create_meal(self, user_id: int, data: MealCreate) -> Meal:
        if not self.user_repo.get(user_id):
            raise NotFoundError(f"User {user_id} not found.")
        payload = data.model_dump()
        payload["logged_at"] = payload["logged_at"] or datetime.now()
        # .replace(tzinfo=None)
        meal = Meal(user_id=user_id, **payload)
        return self.repo.create(meal)

    def get_meal(self, meal_id: int) -> Meal:
        meal = self.repo.get(meal_id)
        if not meal:
            raise NotFoundError(f"Meal {meal_id} not found.")
        return meal

    def list_meals(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Meal]:
        return self.repo.list_for_user(user_id, skip=skip, limit=limit)

    def update_meal(self, meal_id: int, data: MealUpdate) -> Meal:
        meal = self.get_meal(meal_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(meal, field, value)
        return self.repo.update(meal)

    def delete_meal(self, meal_id: int) -> None:
        meal = self.get_meal(meal_id)
        self.repo.delete(meal)
