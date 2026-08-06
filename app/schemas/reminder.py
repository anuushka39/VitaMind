"""Pydantic schemas for the Reminder resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.reminder import ReminderStatus, ReminderType


class ReminderCreate(BaseModel):
    user_id: int
    reminder_type: ReminderType
    scheduled_time: datetime


class ReminderOut(BaseModel):
    id: int
    user_id: int
    reminder_type: ReminderType
    scheduled_time: datetime
    status: ReminderStatus
    retry_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
