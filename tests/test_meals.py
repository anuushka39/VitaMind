"""
Meal upload: Gemini vision analysis (mocked), the health_status-driven
retrieval branching, and the composed conversational reply. All external
calls (Gemini vision, Gemini text generation, FAISS retrieval) are mocked
so this file doesn't depend on real credentials or a built index.
"""

from unittest.mock import AsyncMock, patch

HEALTHY_MEAL = {
    "detected_food": "vegetable daliya",
    "calories": 320,
    "protein_g": 10,
    "carbs_g": 55,
    "fat_g": 6,
    "health_status": "healthy",
    "reason": "Whole grain and vegetable based, low in unhealthy fats.",
}

MODERATE_MEAL = {
    "detected_food": "plain white rice and dal",
    "calories": 480,
    "protein_g": 12,
    "carbs_g": 85,
    "fat_g": 8,
    "health_status": "moderate",
    "reason": "Balanced but low in fiber and lacking vegetables.",
}

UNHEALTHY_MEAL = {
    "detected_food": "pakora",
    "calories": 600,
    "protein_g": 8,
    "carbs_g": 40,
    "fat_g": 38,
    "health_status": "unhealthy",
    "reason": "Deep-fried in refined oil with little fiber or protein.",
}


def _upload(client, user_id, filename="meal.jpg"):
    files = {"file": (filename, b"fake-image-bytes", "image/jpeg")}
    return client.post(f"/api/v1/meals/upload?user_id={user_id}", files=files)


def test_upload_healthy_meal_skips_tip_retrieval(client, make_user):
    user = make_user()
    with patch(
        "app.services.meal_service.gemini_client.analyze_meal_image",
        new=AsyncMock(return_value=HEALTHY_MEAL),
    ), patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(return_value="Your vegetable daliya has been logged! Nice balanced choice."),
    ), patch(
        "app.services.meal_service.recommendation_service.retrieve_tips"
    ) as mock_retrieve:
        response = _upload(client, user.id)

    assert response.status_code == 201
    body = response.json()
    assert body["meal"]["health_status"] == "healthy"
    assert body["reply"] == "Your vegetable daliya has been logged! Nice balanced choice."
    mock_retrieve.assert_not_called()


def test_upload_moderate_meal_retrieves_one_tip(client, make_user):
    user = make_user()
    with patch(
        "app.services.meal_service.gemini_client.analyze_meal_image",
        new=AsyncMock(return_value=MODERATE_MEAL),
    ), patch(
        "app.services.meal_service.recommendation_service.retrieve_tips",
        return_value=["Add a source of protein like curd or sprouts."],
    ) as mock_retrieve, patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(return_value="Logged! Adding curd or sprouts would round this out nicely."),
    ):
        response = _upload(client, user.id)

    assert response.status_code == 201
    body = response.json()
    assert body["meal"]["health_status"] == "moderate"
    mock_retrieve.assert_called_once_with("plain white rice and dal", k=1)
    assert "curd" in body["reply"]


def test_upload_unhealthy_meal_retrieves_three_tips(client, make_user):
    user = make_user()
    with patch(
        "app.services.meal_service.gemini_client.analyze_meal_image",
        new=AsyncMock(return_value=UNHEALTHY_MEAL),
    ), patch(
        "app.services.meal_service.recommendation_service.retrieve_tips",
        return_value=["Try roasted chana with curd instead of fried snacks."],
    ) as mock_retrieve, patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(return_value="Logged! Next time try roasted chana with curd instead."),
    ):
        response = _upload(client, user.id)

    assert response.status_code == 201
    body = response.json()
    assert body["meal"]["health_status"] == "unhealthy"
    mock_retrieve.assert_called_once_with("pakora", k=3)
    assert "roasted chana" in body["reply"]


def test_reply_falls_back_to_plain_sentence_when_gemini_fails(client, make_user):
    user = make_user()
    with patch(
        "app.services.meal_service.gemini_client.analyze_meal_image",
        new=AsyncMock(return_value=HEALTHY_MEAL),
    ), patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(side_effect=RuntimeError("Gemini down")),
    ):
        response = _upload(client, user.id)

    assert response.status_code == 201
    body = response.json()
    assert "vegetable daliya" in body["reply"]


def test_meal_history_ordered_most_recent_first(client, make_user):
    user = make_user()
    with patch(
        "app.services.meal_service.gemini_client.analyze_meal_image",
        new=AsyncMock(side_effect=[HEALTHY_MEAL, UNHEALTHY_MEAL]),
    ), patch(
        "app.services.meal_service.recommendation_service.retrieve_tips",
        return_value=["alt suggestion"],
    ), patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(return_value="logged"),
    ):
        _upload(client, user.id, "first.jpg")
        _upload(client, user.id, "second.jpg")

    history = client.get(f"/api/v1/meals/{user.id}")
    assert history.status_code == 200
    meals = history.json()
    assert len(meals) == 2
    assert meals[0]["detected_food"] == "pakora"
    assert meals[1]["detected_food"] == "vegetable daliya"


def test_meal_history_empty_for_new_user(client, make_user):
    user = make_user()
    response = client.get(f"/api/v1/meals/{user.id}")
    assert response.status_code == 200
    assert response.json() == []


def test_unrecognized_health_status_defaults_to_moderate(client, make_user):
    """Gemini occasionally drifts from the requested enum values -- the
    service should degrade gracefully (default to moderate) rather than
    error out and lose the whole meal log."""
    user = make_user()
    bad_result = {**HEALTHY_MEAL, "health_status": "pretty good"}
    with patch(
        "app.services.meal_service.gemini_client.analyze_meal_image",
        new=AsyncMock(return_value=bad_result),
    ), patch(
        "app.services.meal_service.recommendation_service.retrieve_tips", return_value=[]
    ), patch(
        "app.services.meal_service.gemini_client.generate_text",
        new=AsyncMock(return_value="Logged!"),
    ):
        response = _upload(client, user.id)

    assert response.status_code == 201
    assert response.json()["meal"]["health_status"] == "moderate"