from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class MealCreate(BaseModel):
    meal_type: MealType
    items: list[str] = Field(min_length=1)
    calories: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    carbs_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)
    logged_at: datetime | None = None  # defaults to now() in the service if omitted


class MealUpdate(BaseModel):
    meal_type: MealType | None = None
    items: list[str] | None = Field(default=None, min_length=1)
    calories: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    carbs_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)


class MealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    meal_type: str
    items: list[str]
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    logged_at: datetime
    created_at: datetime
    updated_at: datetime
