"""Pydantic schemas for the ConversationMessage resource."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.conversation import MessageRole, MessageType


class ConversationMessageCreate(BaseModel):
    user_id: int
    role: MessageRole
    message_text: str
    message_type: MessageType = MessageType.text


class ConversationMessageOut(BaseModel):
    id: int
    user_id: int
    role: MessageRole
    message_text: str
    message_type: MessageType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
