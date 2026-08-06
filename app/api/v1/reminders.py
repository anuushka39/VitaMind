"""Reminder endpoints — create, list, and confirm."""

from fastapi import APIRouter, Depends

from app.api.deps import get_reminder_service
from app.schemas.reminder import ReminderCreate, ReminderOut
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderOut, status_code=201)
def create_reminder(
    payload: ReminderCreate, service: ReminderService = Depends(get_reminder_service)
):
    return service.create_reminder(
        payload.user_id, payload.reminder_type, payload.scheduled_time
    )


@router.get("/{user_id}", response_model=list[ReminderOut])
def list_reminders(
    user_id: int, service: ReminderService = Depends(get_reminder_service)
):
    return service.list_reminders(user_id)


@router.post("/{reminder_id}/confirm", response_model=ReminderOut)
def confirm_reminder(
    reminder_id: int, service: ReminderService = Depends(get_reminder_service)
):
    return service.confirm(reminder_id)
