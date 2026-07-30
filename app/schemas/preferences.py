from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DietType = Literal["vegetarian", "non_vegetarian", "vegan"]


class PreferencesUpsert(BaseModel):
    diet_type: DietType = "non_vegetarian"
    allergies: list[str] = Field(default_factory=list)
    disliked_foods: list[str] = Field(default_factory=list)
    fitness_goal: str | None = None


class PreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    diet_type: str
    allergies: list[str]
    disliked_foods: list[str]
    fitness_goal: str | None
    created_at: datetime
    updated_at: datetime
