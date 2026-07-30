from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.weight import WeightLogCreate, WeightLogRead
from app.services.weight_service import WeightService

router = APIRouter(prefix="/weight", tags=["weight"])


@router.post("", response_model=WeightLogRead, status_code=status.HTTP_201_CREATED)
def log_weight(user_id: int, payload: WeightLogCreate, db: Session = Depends(get_db)):
    return WeightService(db).create_log(user_id, payload)


@router.get("", response_model=list[WeightLogRead])
def list_weight(user_id: int, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return WeightService(db).list_logs(user_id, skip=skip, limit=limit)
