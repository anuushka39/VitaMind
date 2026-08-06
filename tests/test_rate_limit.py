"""V2: In-process rate limiting middleware."""


def test_rate_limit_returns_429_after_threshold(client, monkeypatch):
    import app.core.config as config_mod

    monkeypatch.setattr(config_mod.settings, "RATE_LIMIT_PER_MINUTE", 3)

    statuses = [client.get("/api/v1/health").status_code for _ in range(6)]

    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses[3:]


def test_rate_limit_response_shape(client, monkeypatch):
    import app.core.config as config_mod

    monkeypatch.setattr(config_mod.settings, "RATE_LIMIT_PER_MINUTE", 1)

    client.get("/api/v1/health")
    response = client.get("/api/v1/health")

    assert response.status_code == 429
    body = response.json()
    assert body["error"] == "RateLimitExceeded"
