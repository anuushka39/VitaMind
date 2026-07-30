"""Service-layer test — verifies business rules (user must exist), not
just pass-through to the repository."""

import pytest

from app.middleware.error_handlers import NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.meal import MealCreate
from app.services.meal_service import MealService


def test_create_meal_for_existing_user(db_session):
    user = UserRepository(db_session).create(User(name="Anu", email="anu@example.com"))
    service = MealService(db_session)

    meal = service.create_meal(
        user.id,
        MealCreate(meal_type="breakfast", items=["oats", "milk"], calories=320, protein_g=12),
    )

    assert meal.id is not None
    assert meal.calories == 320
    assert meal.items == ["oats", "milk"]


def test_create_meal_for_missing_user_raises(db_session):
    service = MealService(db_session)
    with pytest.raises(NotFoundError):
        service.create_meal(999, MealCreate(meal_type="lunch", items=["rice"]))
