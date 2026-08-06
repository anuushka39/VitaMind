"""V2: Conversation memory endpoints."""


def test_log_and_retrieve_conversation_history(client, make_user):
    user = make_user()

    r1 = client.post(
        "/api/v1/conversation/message",
        json={"user_id": user.id, "role": "user", "message_text": "hi there"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/conversation/message",
        json={"user_id": user.id, "role": "assistant", "message_text": "hello!"},
    )
    assert r2.status_code == 201

    history = client.get(f"/api/v1/conversation/{user.id}")
    assert history.status_code == 200
    messages = history.json()
    assert len(messages) == 2
    # oldest first -- matches what a prompt-context assembler would expect
    assert messages[0]["message_text"] == "hi there"
    assert messages[1]["message_text"] == "hello!"


def test_history_respects_limit(client, make_user):
    user = make_user()
    for i in range(5):
        client.post(
            "/api/v1/conversation/message",
            json={"user_id": user.id, "role": "user", "message_text": f"msg {i}"},
        )

    history = client.get(f"/api/v1/conversation/{user.id}", params={"limit": 2})
    assert history.status_code == 200
    messages = history.json()
    assert len(messages) == 2
    # should be the 2 most recent, oldest-first within that window
    assert messages[-1]["message_text"] == "msg 4"


def test_empty_history_for_new_user(client, make_user):
    user = make_user()
    history = client.get(f"/api/v1/conversation/{user.id}")
    assert history.status_code == 200
    assert history.json() == []
