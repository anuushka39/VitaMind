"""Conversation repository — raw DB access for conversation_messages."""

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessage


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_message(self, message: ConversationMessage) -> ConversationMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_recent(self, user_id: int, limit: int = 20) -> list[ConversationMessage]:
        """
        Returns the most recent `limit` messages, oldest-first, ready to be
        fed straight into a prompt as conversation history.

        Ordered by (created_at DESC, id DESC): created_at alone isn't a
        reliable tiebreaker when two messages are inserted within the same
        timestamp resolution window (SQLite/MySQL DATETIME without
        fractional seconds can tie at 1-second resolution) — id is
        strictly increasing with insertion order, so it's a safe secondary
        sort key.
        """
        rows = (
            self.db.query(ConversationMessage)
            .filter(ConversationMessage.user_id == user_id)
            .order_by(desc(ConversationMessage.created_at), desc(ConversationMessage.id))
            .limit(limit)
            .all()
        )
        return list(reversed(rows))
