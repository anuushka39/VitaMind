from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

GoalType = Literal[
    "daily_calories", "daily_water_ml",  # daily targets, read directly by the dashboard
    "weight_loss", "weight_gain", "muscle_gain", "maintenance",  # longer-horizon goals
]


class GoalCreate(BaseModel):
    goal_type: GoalType
    target_value: float | None = Field(default=None, gt=0)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def check_date_order(self) -> "GoalCreate":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class GoalUpdate(BaseModel):
    target_value: float | None = Field(default=None, gt=0)
    end_date: date | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    goal_type: str
    target_value: float | None
    start_date: date
    end_date: date | None
    created_at: datetime
    updated_at: datetime
