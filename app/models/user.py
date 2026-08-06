"""
User ORM model.

Represents anyone talking to the bot, regardless of platform. platform +
platform_user_id together uniquely identify a real-world user (e.g. a
specific Telegram chat_id or WhatsApp phone number) — that's what the app
looks up on every inbound message to find (or create) the right user.
"""

import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, func

from app.db.base import Base


class Platform(str, enum.Enum):
    telegram = "telegram"
    # whatsapp = "whatsapp"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(Platform), nullable=False)
    platform_user_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)

    # JSON columns keep V1 simple: goals/allergies don't need their own
    # tables yet since nothing in V1 queries into their contents. If a
    # later version needs to filter/search on individual allergies, that's
    # the signal to normalize this into a proper child table.
    goals = Column(JSON, nullable=True)
    allergies = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
