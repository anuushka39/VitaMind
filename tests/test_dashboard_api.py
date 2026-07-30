"""API-layer integration test for the dashboard endpoint — verifies
aggregation across meals/water/exercise/sleep/weight/goals actually works
end to end through real HTTP calls, against the exact response contract
(user/today/goals) later consumers rely on."""


def _create_user(client) -> int:
    response = client.post("/users", json={"name": "Anushka", "email": "anu@example.com"})
    return response.json()["id"]


def test_dashboard_reflects_logged_data(client):
    user_id = _create_user(client)

    client.post(f"/meals?user_id={user_id}", json={
        "meal_type": "breakfast", "items": ["oats", "milk"], "calories": 320, "protein_g": 12,
    })

    client.post(f"/water?user_id={user_id}", json={"amount_ml": 250})
    client.post(f"/exercise?user_id={user_id}", json={"exercise_type": "running", "duration_min": 30})
    client.post(f"/goals?user_id={user_id}", json={
        "goal_type": "daily_calories", "target_value": 2000, "start_date": "2026-01-01",
    })
    client.post(f"/goals?user_id={user_id}", json={
        "goal_type": "daily_water_ml", "target_value": 3000, "start_date": "2026-01-01",
    })

    response = client.get(f"/dashboard?user_id={user_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["user"] == {"id": user_id, "name": "Anushka"}
    assert body["today"]["calories"] == 320
    assert body["today"]["water_ml"] == 250
    assert body["today"]["exercise_minutes"] == 30
    assert body["today"]["sleep_hours"] is None
    assert body["today"]["weight"] is None
    assert body["goals"]["daily_calories"] == 2000
    assert body["goals"]["daily_water_ml"] == 3000


def test_dashboard_for_missing_user_returns_404(client):
    response = client.get("/dashboard?user_id=9999")
    assert response.status_code == 404


def test_dashboard_with_no_goals_returns_null_goal_fields(client):
    user_id = _create_user(client)
    response = client.get(f"/dashboard?user_id={user_id}")
    body = response.json()
    assert body["goals"]["daily_calories"] is None
    assert body["goals"]["daily_water_ml"] is None
