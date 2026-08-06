"""
Reminder service — business logic for creating, listing, and confirming
reminders. The actual scheduling (when jobs fire) lives in app/scheduler/;
this service is what those jobs call into, and what the confirm API
endpoint calls into — keeping "what a reminder is" separate from "when it
fires."
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.reminder import Reminder, ReminderStatus, ReminderType
from app.repositories.reminder_repo import ReminderRepository


class ReminderNotFoundError(NotFoundError):
    message = "Reminder not found."


class ReminderService:
    def __init__(self, db: Session):
        self.repo = ReminderRepository(db)

    def create_reminder(
        self, user_id: int, reminder_type: ReminderType, scheduled_time: datetime
    ) -> Reminder:
        reminder = Reminder(
            user_id=user_id, reminder_type=reminder_type, scheduled_time=scheduled_time
        )
        return self.repo.create(reminder)

    def list_reminders(self, user_id: int) -> list[Reminder]:
        return self.repo.list_by_user(user_id)

    def get_reminder(self, reminder_id: int) -> Reminder:
        reminder = self.repo.get_by_id(reminder_id)
        if not reminder:
            raise ReminderNotFoundError()
        return reminder

    def mark_sent(self, reminder_id: int) -> Reminder:
        reminder = self.get_reminder(reminder_id)
        return self.repo.update_status(reminder, ReminderStatus.sent)

    def confirm(self, reminder_id: int) -> Reminder:
        """
        Called from the confirm API endpoint (user replied "yes"/"sleeping")
        or from a webhook parsing a confirmation reply. Once confirmed, the
        scheduler's retry loop checks this status and stops rescheduling.
        """
        reminder = self.get_reminder(reminder_id)
        return self.repo.update_status(reminder, ReminderStatus.confirmed)

    def snooze_and_bump_retry(self, reminder_id: int) -> Reminder:
        reminder = self.get_reminder(reminder_id)
        return self.repo.update_status(reminder, ReminderStatus.snoozed, bump_retry=True)

    def get_latest_pending_sleep_reminder(self, user_id: int) -> Reminder | None:
        return self.repo.get_latest_pending_sleep_reminder(user_id)