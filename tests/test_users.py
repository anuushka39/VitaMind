"""V1: User CRUD lifecycle, including error paths through the global
exception handlers."""


def test_create_get_update_delete_user(client):
    create_resp = client.post(
        "/api/v1/users",
        json={"platform": "telegram", "platform_user_id": "u1", "name": "Anu"},
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/users/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Anu"

    patch_resp = client.patch(f"/api/v1/users/{user_id}", json={"name": "Anu Updated"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Anu Updated"

    delete_resp = client.delete(f"/api/v1/users/{user_id}")
    assert delete_resp.status_code == 204

    after_delete = client.get(f"/api/v1/users/{user_id}")
    assert after_delete.status_code == 404
    assert after_delete.json()["error"] == "UserNotFoundError"


def test_duplicate_platform_user_id_conflicts(client):
    payload = {"platform": "telegram", "platform_user_id": "dup_1", "name": "First"}
    first = client.post("/api/v1/users", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/users", json={**payload, "name": "Second"})
    assert second.status_code == 409
    assert second.json()["error"] == "DuplicateUserError"


def test_get_nonexistent_user_returns_404(client):
    response = client.get("/api/v1/users/99999")
    assert response.status_code == 404
    assert response.json()["error"] == "UserNotFoundError"


def test_bad_payload_returns_422_not_a_traceback(client):
    response = client.post("/api/v1/users", json={"platform": "not_a_real_platform"})
    assert response.status_code == 422
