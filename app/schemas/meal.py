"""Pydantic schemas for the Meal resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.meal import HealthStatus


class MealAnalysisResult(BaseModel):
    """
    What gemini_client.analyze_meal_image() returns — kept separate from
    MealOut because this is the raw AI output shape, not the DB row shape.
    health_status/reason replace the old locally-computed healthy_score:
    Gemini now classifies the meal itself, reasoning over fiber, processing,
    cooking method, etc., not just macros.
    """

    detected_food: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    health_status: HealthStatus
    reason: str


class MealOut(BaseModel):
    id: int
    user_id: int
    image_url: str | None = None
    detected_food: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    health_status: HealthStatus
    reason: str | None = None
    meal_time: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealUploadResponse(BaseModel):
    """
    meal: the logged, structured record.
    reply: the natural, conversational message to show the user (what the
    bot actually says) — always present, not just for unhealthy meals. See
    MealService._compose_reply for how it's generated and the fallback used
    if Gemini's phrasing call fails.
    """

    meal: MealOut
    reply: str