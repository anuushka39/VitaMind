"""
Shared FastAPI dependencies.

get_db is re-exported from app.db.session so every route imports
dependencies from this one module, rather than reaching into app.db.session
or app.services.* directly. get_user_service is a small factory that wires
a request-scoped DB session into a fresh UserService instance per request.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.conversation_service import ConversationService
from app.services.meal_service import MealService
from app.services.reminder_service import ReminderService
from app.services.user_service import UserService

__all__ = [
    "get_db",
    "get_user_service",
    "get_meal_service",
    "get_conversation_service",
    "get_reminder_service",
]


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_meal_service(db: Session = Depends(get_db)) -> MealService:
    return MealService(db)


def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


def get_reminder_service(db: Session = Depends(get_db)) -> ReminderService:
    return ReminderService(db)
