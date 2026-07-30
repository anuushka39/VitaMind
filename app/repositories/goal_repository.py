"""Goal has no logged_at field (it has start_date/end_date instead), so it
gets its own list_for_user rather than reusing the log-table pattern."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    model = Goal

    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Goal]:
        stmt = (
            select(Goal)
            .where(Goal.user_id == user_id)
            .order_by(Goal.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_active_by_type(self, user_id: int, goal_type: str) -> Goal | None:
        """Most recent goal of a given type that hasn't ended — used by the
        dashboard to answer 'what's this user's current daily_calories goal'."""
        stmt = (
            select(Goal)
            .where(Goal.user_id == user_id, Goal.goal_type == goal_type)
            .order_by(Goal.start_date.desc())
        )
        return self.db.scalars(stmt).first()
