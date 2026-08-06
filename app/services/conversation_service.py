"""
Conversation service — reads/writes conversation memory and assembles
context for personalization.

This is the layer meal_service and reminder flows call when they need
"what does this user care about" (goals/allergies come from User; recent
chat context comes from here) — kept separate from UserService because
conversation history and user profile are different concerns that happen
to both relate to the same user_id.
"""

from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessage, MessageRole, MessageType
from app.repositories.conversation_repo import ConversationRepository


class ConversationService:
    def __init__(self, db: Session):
        self.repo = ConversationRepository(db)

    def log_message(
        self,
        user_id: int,
        role: MessageRole,
        text: str,
        message_type: MessageType = MessageType.text,
    ) -> ConversationMessage:
        message = ConversationMessage(
            user_id=user_id, role=role, message_text=text, message_type=message_type
        )
        return self.repo.add_message(message)

    def get_recent_history(self, user_id: int, limit: int = 20) -> list[ConversationMessage]:
        return self.repo.get_recent(user_id, limit)

    def build_context_string(self, user_id: int, limit: int = 10) -> str:
        """
        Flattens recent history into a plain string suitable for dropping
        into a Gemini prompt. Kept as a simple join, not a token-aware
        summarizer — appropriate for the short histories this project deals
        with; a real product at scale would need summarization instead.
        """
        history = self.get_recent_history(user_id, limit)
        return "\n".join(f"{m.role.value}: {m.message_text}" for m in history)
