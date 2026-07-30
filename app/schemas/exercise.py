from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExerciseLogCreate(BaseModel):
    exercise_type: str = Field(min_length=1, max_length=50)
    duration_min: int = Field(gt=0, le=1440)
    calories_burned: float | None = Field(default=None, ge=0)
    logged_at: datetime | None = None


class ExerciseLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    exercise_type: str
    duration_min: int
    calories_burned: float | None
    logged_at: datetime
    created_at: datetime
