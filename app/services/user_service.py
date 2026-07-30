"""
User business logic.

Why this file exists: routers shouldn't know HOW a user is created (e.g.
that email uniqueness must be checked first) — that's a business rule,
and business rules live in services, not routers or repositories.
"""

from sqlalchemy.orm import Session

from app.middleware.error_handlers import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise ConflictError(f"A user with email {data.email} already exists.")
        user = User(**data.model_dump())
        return self.repo.create(user)

    def get_user(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found.")
        return user

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.get_user(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return self.repo.update(user)

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        self.repo.delete(user)
