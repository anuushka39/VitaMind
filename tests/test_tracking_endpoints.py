"""API integration tests for the endpoints added in the Version 2 audit fix:
GET /exercise, GET /water, GET /sleep, GET /weight, and full goal CRUD.
Also covers the DB-level CHECK constraints via the API validation path."""


def _create_user(client) -> int:
    response = client.post("/users", json={"name": "Anu", "email": "anu2@example.com"})
    return response.json()["id"]


def test_list_exercise_logs(client):
    user_id = _create_user(client)
    client.post(f"/exercise?user_id={user_id}", json={"exercise_type": "running", "duration_min": 30})
    client.post(f"/exercise?user_id={user_id}", json={"exercise_type": "yoga", "duration_min": 20})

    response = client.get(f"/exercise?user_id={user_id}")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_water_logs(client):
    user_id = _create_user(client)
    client.post(f"/water?user_id={user_id}", json={"amount_ml": 250})

    response = client.get(f"/water?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()[0]["amount_ml"] == 250


def test_list_sleep_logs(client):
    user_id = _create_user(client)
    client.post(f"/sleep?user_id={user_id}", json={"hours": 7.5})

    response = client.get(f"/sleep?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()[0]["hours"] == 7.5


def test_list_weight_logs(client):
    user_id = _create_user(client)
    client.post(f"/weight?user_id={user_id}", json={"weight_kg": 61.8})

    response = client.get(f"/weight?user_id={user_id}")
    assert response.status_code == 200
    assert response.json()[0]["weight_kg"] == 61.8


def test_list_logs_for_missing_user_returns_404(client):
    response = client.get("/exercise?user_id=9999")
    assert response.status_code == 404


def test_goal_full_crud(client):
    user_id = _create_user(client)

    create_resp = client.post(f"/goals?user_id={user_id}", json={
        "goal_type": "daily_calories", "target_value": 2000, "start_date": "2026-01-01",
    })
    assert create_resp.status_code == 201
    goal_id = create_resp.json()["id"]

    list_resp = client.get(f"/goals?user_id={user_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.put(f"/goals/{goal_id}", json={"target_value": 2200})
    assert update_resp.status_code == 200
    assert update_resp.json()["target_value"] == 2200

    delete_resp = client.delete(f"/goals/{goal_id}")
    assert delete_resp.status_code == 204

    list_after_delete = client.get(f"/goals?user_id={user_id}")
    assert len(list_after_delete.json()) == 0


def test_goal_update_missing_goal_returns_404(client):
    response = client.put("/goals/9999", json={"target_value": 100})
    assert response.status_code == 404


def test_negative_water_rejected_by_schema(client):
    user_id = _create_user(client)
    response = client.post(f"/water?user_id={user_id}", json={"amount_ml": -100})
    assert response.status_code == 422


def test_sleep_hours_over_24_rejected_by_schema(client):
    user_id = _create_user(client)
    response = client.post(f"/sleep?user_id={user_id}", json={"hours": 30})
    assert response.status_code == 422


def test_goal_end_date_before_start_date_rejected(client):
    user_id = _create_user(client)
    response = client.post(f"/goals?user_id={user_id}", json={
        "goal_type": "daily_calories", "target_value": 2000,
        "start_date": "2026-02-01", "end_date": "2026-01-01",
    })
    assert response.status_code == 422
