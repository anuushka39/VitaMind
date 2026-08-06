"""
User service — business logic layer.

Routes call this, never the repository directly. Right now the logic is
thin (V1 is just CRUD), but this is the layer that will grow in later
versions — e.g. "look up or create a user from an inbound Telegram message"
belongs here, not in the webhook route or the repository.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateUserError, UserNotFoundError
from app.models.user import Platform
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_or_create_by_platform(
        self, platform: Platform, platform_user_id: str, name: str | None = None
    ):
        """
        Used by the Telegram webhooks: on every inbound message we
        need "the user this chat_id/phone number belongs to," creating them
        transparently on first contact rather than requiring a separate
        signup step (there isn't one — the bot IS the signup flow).
        """
        existing = self.repo.get_by_platform_user_id(platform_user_id)
        if existing:
            return existing
        return self.repo.create(
            UserCreate(platform=platform, platform_user_id=platform_user_id, name=name)
        )

    def create_user(self, data: UserCreate):
        existing = self.repo.get_by_platform_user_id(data.platform_user_id)
        if existing:
            raise DuplicateUserError()
        return self.repo.create(data)

    def get_user(self, user_id: int):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user

    def update_user(self, user_id: int, data: UserUpdate):
        user = self.get_user(user_id)
        return self.repo.update(user, data)

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        self.repo.delete(user)
