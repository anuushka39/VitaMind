from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_telegram_id(self, telegram_id: str) -> User | None:
        return self.db.scalar(select(User).where(User.telegram_id == telegram_id))
