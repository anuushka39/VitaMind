"""
Meal ORM model.

health_status replaces the old numeric healthy_score: Gemini now classifies
the meal itself (reasoning over fiber, processing, cooking method, etc.,
not just macros), so the DB stores that classification directly instead of
a locally-computed heuristic score. reason stores Gemini's one-line
justification, both for transparency and because it's reused as grounding
when composing the conversational reply.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func

from app.db.base import Base


class HealthStatus(enum.StrEnum):
    healthy = "healthy"
    moderate = "moderate"
    unhealthy = "unhealthy"


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    image_url = Column(String(255), nullable=True)
    detected_food = Column(String(255), nullable=False)

    calories = Column(Float, nullable=False, default=0)
    protein_g = Column(Float, nullable=False, default=0)
    carbs_g = Column(Float, nullable=False, default=0)
    fat_g = Column(Float, nullable=False, default=0)

    health_status = Column(Enum(HealthStatus), nullable=False, index=True)
    reason = Column(Text, nullable=True)

    meal_time = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)