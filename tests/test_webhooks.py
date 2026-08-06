"""
Telegram + WhatsApp webhook entrypoints, including the BackgroundTasks-
driven meal-photo pipeline (now delegating reply text entirely to
MealService), the new nutrition-breakdown-on-request text branch, and the
WhatsApp verification handshake.
"""

from unittest.mock import AsyncMock, patch

MEAL_RESULT = {
    "detected_food": "vegetable daliya",
    "calories": 320,
    "protein_g": 10,
    "carbs_g": 55,
    "fat_g": 6,
    "health_status": "healthy",
    "reason": "Whole grain and vegetable based, low in unhealthy fats.",
}


def test_telegram_text_message_creates_user_and_logs_conversation(client):
    with patch("app.api.webhooks.telegram.telegram_client.send_message", new=AsyncMock()) as mock_send:
        update = {
            "message": {
                "chat": {"id": 555},
                "from": {"first_name": "NewUser"},
                "text": "hello bot",
            }
        }
        response = client.post("/api/v1/webhooks/telegram", json=update)

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_send.assert_awaited_once()

    history = client.get("/api/v1/conversation/1")
    assert history.status_code == 200
    assert history.json()[0]["message_text"] == "hello bot"


def test_telegram_photo_message_uses_meal_service_composed_reply(client):
    with patch(
        "app.api.webhooks.telegram.telegram_client.download_file", new=AsyncMock(return_value=b"img")
    ), patch(
        "app.services.meal_service.gemini_client.analyze_meal_image", new=AsyncMock(return_value=MEAL_RESULT)
    ), patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(return_value="Your vegetable daliya has been logged! Nicely balanced."),
    ), patch(
        "app.api.webhooks.telegram.telegram_client.send_message", new=AsyncMock()
    ) as mock_send:
        update = {"message": {"chat": {"id": 555}, "photo": [{"file_id": "small"}, {"file_id": "large"}]}}
        response = client.post("/api/v1/webhooks/telegram", json=update)

    assert response.status_code == 200
    mock_send.assert_awaited_once()
    reply_text = mock_send.call_args.args[1]
    assert reply_text == "Your vegetable daliya has been logged! Nicely balanced."

    meals = client.get("/api/v1/meals/1")
    assert len(meals.json()) == 1
    assert meals.json()[0]["health_status"] == "healthy"


def test_telegram_webhook_ignores_unhandled_update_types(client):
    response = client.post("/api/v1/webhooks/telegram", json={"update_id": 1, "edited_message": {}})
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_telegram_text_asks_for_calories_returns_last_meal_breakdown(client, make_user, db_session):
    from app.models.meal import HealthStatus, Meal

    user = make_user(platform_user_id="777")
    meal = Meal(
        user_id=user.id,
        detected_food="grilled paneer bowl",
        calories=410,
        protein_g=28,
        carbs_g=30,
        fat_g=14,
        health_status=HealthStatus.healthy,
        reason="Good protein and vegetable balance.",
    )
    db_session.add(meal)
    db_session.commit()

    with patch("app.api.webhooks.telegram.telegram_client.send_message", new=AsyncMock()) as mock_send:
        update = {"message": {"chat": {"id": 777}, "text": "what were the calories in that?"}}
        response = client.post("/api/v1/webhooks/telegram", json=update)

    assert response.status_code == 200
    reply_text = mock_send.call_args.args[1]
    assert "410" in reply_text
    assert "grilled paneer bowl" in reply_text


def test_telegram_text_without_nutrition_keywords_gets_generic_ack(client):
    with patch("app.api.webhooks.telegram.telegram_client.send_message", new=AsyncMock()) as mock_send:
        update = {"message": {"chat": {"id": 888}, "text": "thanks!"}}
        response = client.post("/api/v1/webhooks/telegram", json=update)

    assert response.status_code == 200
    reply_text = mock_send.call_args.args[1]
    assert reply_text == "Got it! Send a meal photo anytime to log it."


