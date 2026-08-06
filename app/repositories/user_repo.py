"""
User repository — the only place in the app that writes SQLAlchemy queries
for the User table.

Why this layer exists (it was explicitly "only if justified" in the
architecture): it keeps query syntax out of business logic, and it means
UserService can be unit-tested by mocking UserRepository instead of needing
a real MySQL connection. For a project this size that's the entire
justification — there's no larger abstraction being built here.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_platform_user_id(self, platform_user_id: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.platform_user_id == platform_user_id)
            .first()
        )

    def update(self, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
