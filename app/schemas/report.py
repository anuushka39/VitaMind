"""Pydantic schema for the weekly nutrition report response."""

from datetime import datetime

from pydantic import BaseModel


class WeeklyReportOut(BaseModel):
    user_id: int
    window_start: datetime
    window_end: datetime
    total_meals: int
    avg_calories: float
    avg_protein_g: float
    avg_carbs_g: float
    avg_fat_g: float
    healthy_meals: int
    moderate_meals: int
    unhealthy_meals: int
    healthy_meal_pct: float | None
    meal_consistency_pct: float