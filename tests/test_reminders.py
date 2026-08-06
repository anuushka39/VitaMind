"""V2: Reminder create/list/confirm and the not-found path."""

from datetime import datetime, timedelta


def test_create_list_confirm_reminder(client, make_user):
    user = make_user()
    scheduled = (datetime.utcnow() + timedelta(hours=1)).isoformat()

    create_resp = client.post(
        "/api/v1/reminders",
        json={"user_id": user.id, "reminder_type": "sleep", "scheduled_time": scheduled},
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["status"] == "pending"
    assert body["retry_count"] == 0
    reminder_id = body["id"]

    list_resp = client.get(f"/api/v1/reminders/{user.id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    confirm_resp = client.post(f"/api/v1/reminders/{reminder_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"


def test_confirm_nonexistent_reminder_returns_404(client):
    response = client.post("/api/v1/reminders/99999/confirm")
    assert response.status_code == 404
    assert response.json()["error"] == "ReminderNotFoundError"


def test_list_reminders_empty_for_new_user(client, make_user):
    user = make_user()
    response = client.get(f"/api/v1/reminders/{user.id}")
    assert response.status_code == 200
    assert response.json() == []
