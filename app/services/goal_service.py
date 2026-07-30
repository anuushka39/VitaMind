from sqlalchemy.orm import Session

from app.middleware.error_handlers import NotFoundError
from app.models.goal import Goal
from app.repositories.goal_repository import GoalRepository
from app.repositories.user_repository import UserRepository
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalService:
    def __init__(self, db: Session):
        self.repo = GoalRepository(db)
        self.user_repo = UserRepository(db)

    def create_goal(self, user_id: int, data: GoalCreate) -> Goal:
        if not self.user_repo.get(user_id):
            raise NotFoundError(f"User {user_id} not found.")
        goal = Goal(user_id=user_id, **data.model_dump())
        return self.repo.create(goal)

    def get_goal(self, goal_id: int) -> Goal:
        goal = self.repo.get(goal_id)
        if not goal:
            raise NotFoundError(f"Goal {goal_id} not found.")
        return goal

    def list_goals(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Goal]:
        if not self.user_repo.get(user_id):
            raise NotFoundError(f"User {user_id} not found.")
        return self.repo.list_for_user(user_id, skip=skip, limit=limit)

    def update_goal(self, goal_id: int, data: GoalUpdate) -> Goal:
        goal = self.get_goal(goal_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(goal, field, value)
        return self.repo.update(goal)

    def delete_goal(self, goal_id: int) -> None:
        goal = self.get_goal(goal_id)
        self.repo.delete(goal)
