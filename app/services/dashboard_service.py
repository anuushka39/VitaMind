"""
Dashboard aggregation — pure read, no writes, no external calls.

Deliberately built as straightforward repository queries assembled into one
response object rather than a dedicated analytics/materialized layer — at
this data volume that would be complexity without a payoff. Revisit only if
this endpoint's query cost becomes a real, measured problem.

Response shape is fixed by the dashboard schema contract (user/today/goals)
since Version 4's bots consume this directly.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.middleware.error_handlers import NotFoundError
from app.repositories.exercise_repository import ExerciseLogRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.meal_repository import MealRepository
from app.repositories.sleep_repository import SleepLogRepository
from app.repositories.user_repository import UserRepository
from app.repositories.water_repository import WaterLogRepository
from app.repositories.weight_repository import WeightLogRepository
from app.schemas.dashboard import DashboardGoals, DashboardResponse, DashboardToday, DashboardUser


class DashboardService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.meal_repo = MealRepository(db)
        self.exercise_repo = ExerciseLogRepository(db)
        self.water_repo = WaterLogRepository(db)
        self.sleep_repo = SleepLogRepository(db)
        self.weight_repo = WeightLogRepository(db)
        self.goal_repo = GoalRepository(db)

    def get_today(self, user_id: int, day: date | None = None) -> DashboardResponse:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found.")

        target_day = day or date.today()

        meals = self.meal_repo.list_for_user_on_date(user_id, target_day)
        exercises = self.exercise_repo.list_for_user_on_date(user_id, target_day)
        waters = self.water_repo.list_for_user_on_date(user_id, target_day)
        sleeps = self.sleep_repo.list_for_user_on_date(user_id, target_day)
        weights = self.weight_repo.list_for_user(user_id, skip=0, limit=1)

        calorie_goal = self.goal_repo.get_active_by_type(user_id, "daily_calories")
        water_goal = self.goal_repo.get_active_by_type(user_id, "daily_water_ml")

        return DashboardResponse(
            user=DashboardUser(id=user.id, name=user.name),
            today=DashboardToday(
                calories=sum(m.calories or 0 for m in meals),
                water_ml=sum(w.amount_ml for w in waters),
                exercise_minutes=sum(e.duration_min for e in exercises),
                sleep_hours=sleeps[0].hours if sleeps else None,
                weight=weights[0].weight_kg if weights else None,
            ),
            goals=DashboardGoals(
                daily_calories=calorie_goal.target_value if calorie_goal else None,
                daily_water_ml=water_goal.target_value if water_goal else None,
            ),
        )
