from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WaterLogCreate(BaseModel):
    amount_ml: int = Field(gt=0, le=10000)
    logged_at: datetime | None = None


class WaterLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount_ml: int
    logged_at: datetime
    created_at: datetime
