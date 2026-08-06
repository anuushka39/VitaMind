"""
ConversationMessage ORM model.

This table IS the "stateful conversation memory" from the resume line — it's
what conversation_service reads to assemble context for a reply, and it's
what makes memory survive app restarts / work across multiple workers
(unlike an in-process dict keyed by chat_id, which breaks the moment you
scale beyond one process or restart the app).
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text, func

from app.db.base import Base


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    system = "system"


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    role = Column(Enum(MessageRole), nullable=False)
    message_text = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.text)

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
