"""
Reminder repository.

Not in the original folder-addition list in the roadmap, but added here for
consistency with every other resource in the app (meal, conversation, user
all have one) — reminder_service needs the same create/get/list/update
primitives, and skipping the repo here would be the one inconsistent
exception in the codebase for no real reason.
"""

from sqlalchemy.orm import Session

from app.models.reminder import Reminder, ReminderStatus, ReminderType


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, reminder: Reminder) -> Reminder:
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        return self.db.get(Reminder, reminder_id)

    def list_by_user(self, user_id: int) -> list[Reminder]:
        return (
            self.db.query(Reminder).filter(Reminder.user_id == user_id).all()
        )

    def update_status(
        self, reminder: Reminder, status: ReminderStatus, bump_retry: bool = False
    ) -> Reminder:
        reminder.status = status
        if bump_retry:
            reminder.retry_count += 1
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def get_latest_pending_sleep_reminder(self, user_id: int) -> Reminder | None:
        return (
            self.db.query(Reminder)
            .filter(
                Reminder.user_id == user_id,
                Reminder.reminder_type == ReminderType.sleep,
                Reminder.status.in_(
                    [ReminderStatus.sent, ReminderStatus.snoozed]
                ),
            )
            .order_by(Reminder.created_at.desc())
            .first()
        )
