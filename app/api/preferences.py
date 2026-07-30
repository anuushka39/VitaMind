from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.preferences import PreferencesRead, PreferencesUpsert
from app.services.preferences_service import PreferencesService

router = APIRouter(prefix="/users/{user_id}/preferences", tags=["preferences"])


@router.put("", response_model=PreferencesRead)
def upsert_preferences(user_id: int, payload: PreferencesUpsert, db: Session = Depends(get_db)):
    return PreferencesService(db).upsert(user_id, payload)


@router.get("", response_model=PreferencesRead)
def get_preferences(user_id: int, db: Session = Depends(get_db)):
    return PreferencesService(db).get(user_id)
