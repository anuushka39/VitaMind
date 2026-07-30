"""
Aggregates every model import.

Why this file exists (and why it's not just a formality):
    SQLAlchemy's declarative registry, and Alembic's autogenerate, only
    know about a model class once Python has actually imported it. If
    Alembic's env.py only imports app.database.base (for Base.metadata)
    without something importing every individual model module, autogenerate
    silently produces an EMPTY migration — no error, just a missing table.
    This file exists purely so one import (`from app.models import *`
    or importing this module) guarantees every model is registered.
"""

from app.models.exercise import ExerciseLog
from app.models.goal import Goal
from app.models.meal import Meal
from app.models.preferences import Preferences
from app.models.sleep import SleepLog
from app.models.user import User
from app.models.water import WaterLog
from app.models.weight import WeightLog

__all__ = [
    "User",
    "Preferences",
    "Meal",
    "ExerciseLog",
    "WaterLog",
    "SleepLog",
    "WeightLog",
    "Goal",
]
