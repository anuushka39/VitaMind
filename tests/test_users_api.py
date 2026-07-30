"""API-layer integration test — real HTTP request/response through the
full stack (router -> service -> repository -> in-memory DB)."""


def test_create_and_get_user(client):
    response = client.post("/users", json={"name": "Anu", "email": "anu@example.com"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "anu@example.com"
    user_id = body["id"]

    fetched = client.get(f"/users/{user_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Anu"


def test_create_duplicate_email_returns_409(client):
    client.post("/users", json={"name": "Anu", "email": "anu@example.com"})
    response = client.post("/users", json={"name": "Someone Else", "email": "anu@example.com"})
    assert response.status_code == 409


def test_get_missing_user_returns_404(client):
    response = client.get("/users/9999")
    assert response.status_code == 404


def test_invalid_email_returns_422(client):
    response = client.post("/users", json={"name": "Anu", "email": "not-an-email"})
    assert response.status_code == 422
