"""
Tests for the health endpoint.

Why this file exists:
    Confirms the app boots, routing works, and the health endpoint reports
    both "database connected" and "database unreachable" cases correctly.
    check_db_connection is mocked so this test needs no real SQLite file
    on disk and no network — pure, fast, deterministic.

V1->V2 change: check_db_connection is now a plain sync function, so it's
mocked with MagicMock/patch's default, not AsyncMock.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_db_connected():
    with patch("app.api.health.check_db_connection", return_value=True):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_health_check_db_unreachable():
    with patch("app.api.health.check_db_connection", return_value=False):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unreachable"


def test_health_response_includes_request_id_header():
    with patch("app.api.health.check_db_connection", return_value=True):
        response = client.get("/health")

    assert "X-Request-ID" in response.headers
