from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.meal import MealCreate, MealRead, MealUpdate
from app.services.meal_service import MealService

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post("", response_model=MealRead, status_code=status.HTTP_201_CREATED)
def create_meal(user_id: int, payload: MealCreate, db: Session = Depends(get_db)):
    return MealService(db).create_meal(user_id, payload)


@router.get("", response_model=list[MealRead])
def list_meals(user_id: int, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return MealService(db).list_meals(user_id, skip=skip, limit=limit)


@router.put("/{meal_id}", response_model=MealRead)
def update_meal(meal_id: int, payload: MealUpdate, db: Session = Depends(get_db)):
    return MealService(db).update_meal(meal_id, payload)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    MealService(db).delete_meal(meal_id)
