"""
Conversation memory endpoints.

Mostly useful for testing/inspecting memory directly via Swagger without
going through a real Telegram round trip — the webhooks are the
primary way messages get logged in practice, but this endpoint lets you
verify the memory layer works in isolation.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_conversation_service
from app.schemas.conversation import ConversationMessageCreate, ConversationMessageOut
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/message", response_model=ConversationMessageOut, status_code=201)
def log_message(
    payload: ConversationMessageCreate,
    service: ConversationService = Depends(get_conversation_service),
):
    return service.log_message(
        payload.user_id, payload.role, payload.message_text, payload.message_type
    )


@router.get("/{user_id}", response_model=list[ConversationMessageOut])
def get_history(
    user_id: int,
    limit: int = 20,
    service: ConversationService = Depends(get_conversation_service),
):
    return service.get_recent_history(user_id, limit)
