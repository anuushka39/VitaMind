from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.middleware.error_handlers import NotFoundError
from app.models.sleep import SleepLog
from app.repositories.sleep_repository import SleepLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.sleep import SleepLogCreate


class SleepService:
    def __init__(self, db: Session):
        self.repo = SleepLogRepository(db)
        self.user_repo = UserRepository(db)

    def create_log(self, user_id: int, data: SleepLogCreate) -> SleepLog:
        if not self.user_repo.get(user_id):
            raise NotFoundError(f"User {user_id} not found.")
        payload = data.model_dump()
        payload["logged_at"] = payload["logged_at"] or datetime.now(UTC).replace(tzinfo=None)
        log = SleepLog(user_id=user_id, **payload)
        return self.repo.create(log)

    def list_logs(self, user_id: int, skip: int = 0, limit: int = 100) -> list[SleepLog]:
        if not self.user_repo.get(user_id):
            raise NotFoundError(f"User {user_id} not found.")
        return self.repo.list_for_user(user_id, skip=skip, limit=limit)
