import pytest
from fastapi.testclient import TestClient

from services.runtime.src.main import app


client = TestClient(app)


def test_health_root_ok(monkeypatch):
    async def fake_fetchrow(query: str):  # noqa: ARG001
        return 1

    from services.runtime.src.api import health as health_module

    monkeypatch.setattr(health_module.db, "fetchrow", fake_fetchrow)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["database"] is True


def test_v1_health_ok(monkeypatch):
    async def fake_fetchrow(query: str):  # noqa: ARG001
        return 1

    from services.runtime.src.api import health as health_module

    monkeypatch.setattr(health_module.db, "fetchrow", fake_fetchrow)

    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_health_ready_ok(monkeypatch):
    async def fake_fetchrow(query: str):  # noqa: ARG001
        return 1

    from services.runtime.src.api import health as health_module

    monkeypatch.setattr(health_module.db, "fetchrow", fake_fetchrow)

    response = client.get("/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_v1_health_unhealthy(monkeypatch):
    async def failing_fetchrow(query: str):  # noqa: ARG001
        raise RuntimeError("db down")

    from services.runtime.src.api import health as health_module

    monkeypatch.setattr(health_module.db, "fetchrow", failing_fetchrow)

    response = client.get("/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["status"] == "unhealthy"


def test_v1_health_ready_unhealthy(monkeypatch):
    async def failing_fetchrow(query: str):  # noqa: ARG001
        raise RuntimeError("db down")

    from services.runtime.src.api import health as health_module

    monkeypatch.setattr(health_module.db, "fetchrow", failing_fetchrow)

    response = client.get("/v1/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["detail"]["status"] == "not_ready"
