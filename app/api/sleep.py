from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.sleep import SleepLogCreate, SleepLogRead
from app.services.sleep_service import SleepService

router = APIRouter(prefix="/sleep", tags=["sleep"])


@router.post("", response_model=SleepLogRead, status_code=status.HTTP_201_CREATED)
def log_sleep(user_id: int, payload: SleepLogCreate, db: Session = Depends(get_db)):
    return SleepService(db).create_log(user_id, payload)


@router.get("", response_model=list[SleepLogRead])
def list_sleep(user_id: int, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return SleepService(db).list_logs(user_id, skip=skip, limit=limit)
