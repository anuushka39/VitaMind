from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SleepQuality = Literal["poor", "average", "good"]


class SleepLogCreate(BaseModel):
    hours: float = Field(gt=0, le=24)
    quality: SleepQuality | None = None
    logged_at: datetime | None = None


class SleepLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    hours: float
    quality: str | None
    logged_at: datetime
    created_at: datetime
