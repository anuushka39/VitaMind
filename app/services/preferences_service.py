from sqlalchemy.orm import Session

from app.middleware.error_handlers import NotFoundError
from app.models.preferences import Preferences
from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.user_repository import UserRepository
from app.schemas.preferences import PreferencesUpsert


class PreferencesService:
    def __init__(self, db: Session):
        self.repo = PreferencesRepository(db)
        self.user_repo = UserRepository(db)

    def upsert(self, user_id: int, data: PreferencesUpsert) -> Preferences:
        if not self.user_repo.get(user_id):
            raise NotFoundError(f"User {user_id} not found.")

        existing = self.repo.get_by_user_id(user_id)
        if existing:
            for field, value in data.model_dump().items():
                setattr(existing, field, value)
            return self.repo.update(existing)

        prefs = Preferences(user_id=user_id, **data.model_dump())
        return self.repo.create(prefs)

    def get(self, user_id: int) -> Preferences:
        prefs = self.repo.get_by_user_id(user_id)
        if not prefs:
            raise NotFoundError(f"No preferences set for user {user_id}.")
        return prefs
