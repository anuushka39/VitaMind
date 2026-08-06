"""
Reminder ORM model.

status + retry_count together implement the "keep reminding every 30 min
until confirmed" rule from the spec, without any extra state machine
library: a scheduled job checks status, and if it's still 'pending' after
its window, it resends and reschedules itself with retry_count + 1.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, func

from app.db.base import Base


class ReminderType(str, enum.Enum):
    morning = "morning"
    water = "water"
    lunch = "lunch"
    coffee = "coffee"
    dinner = "dinner"
    sleep = "sleep"


class ReminderStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    confirmed = "confirmed"
    snoozed = "snoozed"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    reminder_type = Column(Enum(ReminderType), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(Enum(ReminderStatus), nullable=False, default=ReminderStatus.pending)
    retry_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
