from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.exercise import ExerciseLogCreate, ExerciseLogRead
from app.services.exercise_service import ExerciseService

router = APIRouter(prefix="/exercise", tags=["exercise"])


@router.post("", response_model=ExerciseLogRead, status_code=status.HTTP_201_CREATED)
def log_exercise(user_id: int, payload: ExerciseLogCreate, db: Session = Depends(get_db)):
    return ExerciseService(db).create_log(user_id, payload)


@router.get("", response_model=list[ExerciseLogRead])
def list_exercise(user_id: int, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return ExerciseService(db).list_logs(user_id, skip=skip, limit=limit)
