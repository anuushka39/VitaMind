from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.water import WaterLogCreate, WaterLogRead
from app.services.water_service import WaterService

router = APIRouter(prefix="/water", tags=["water"])


@router.post("", response_model=WaterLogRead, status_code=status.HTTP_201_CREATED)
def log_water(user_id: int, payload: WaterLogCreate, db: Session = Depends(get_db)):
    return WaterService(db).create_log(user_id, payload)


@router.get("", response_model=list[WaterLogRead])
def list_water(user_id: int, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return WaterService(db).list_logs(user_id, skip=skip, limit=limit)
