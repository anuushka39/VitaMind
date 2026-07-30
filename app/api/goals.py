from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(user_id: int, payload: GoalCreate, db: Session = Depends(get_db)):
    return GoalService(db).create_goal(user_id, payload)


@router.get("", response_model=list[GoalRead])
def list_goals(user_id: int, skip: int = 0, limit: int = Query(default=100, le=500), db: Session = Depends(get_db)):
    return GoalService(db).list_goals(user_id, skip=skip, limit=limit)


@router.put("/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)):
    return GoalService(db).update_goal(goal_id, payload)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    GoalService(db).delete_goal(goal_id)
