import time

from fastapi.testclient import TestClient

from app import create_app


def test_version_health_metrics(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc123")
    with TestClient(create_app()) as client:
        data = client.get("/api/version").json()
        assert data["version"] == "abc123"
        assert data["hostname"] and data["timestamp"]
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200
        assert "app_http_requests_total" in client.get("/metrics").text
        assert client.get("/missing").status_code == 404


def test_unready_remains_live(monkeypatch):
    monkeypatch.setenv("FAIL_READINESS", "true")
    with TestClient(create_app()) as client:
        assert client.get("/health/ready").status_code == 503
        assert client.get("/api/version").status_code == 503
        assert client.get("/health/live").status_code == 200


def test_startup_delay(monkeypatch):
    monkeypatch.setenv("STARTUP_DELAY_SECONDS", "0.05")
    with TestClient(create_app()) as client:
        assert client.get("/health/ready").status_code == 503
        time.sleep(0.06)
        assert client.get("/health/ready").status_code == 200


def test_exception_is_sanitized():
    app = create_app()

    @app.get("/broken")
    async def broken():
        raise RuntimeError("private detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/broken")
        assert response.status_code == 500
        assert "private detail" not in response.text
