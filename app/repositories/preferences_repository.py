from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.preferences import Preferences
from app.repositories.base import BaseRepository


class PreferencesRepository(BaseRepository[Preferences]):
    model = Preferences

    def get_by_user_id(self, user_id: int) -> Preferences | None:
        return self.db.scalar(select(Preferences).where(Preferences.user_id == user_id))
