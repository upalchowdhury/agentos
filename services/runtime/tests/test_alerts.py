import pytest

from services.runtime.src.alerts import AlertManager, AlertThresholds


@pytest.mark.asyncio
async def test_alert_manager_skip_without_webhook(monkeypatch):
    manager = AlertManager(webhook_url=None)

    async def fail_fetch(*args, **kwargs):  # pragma: no cover - to ensure not called
        raise AssertionError("fetch should not be called when webhook missing")

    monkeypatch.setattr("services.runtime.src.alerts.db.fetch", fail_fetch)

    await manager.evaluate(agent_id="a", agent_name="Agent", telemetry_quality="verified")


@pytest.mark.asyncio
async def test_alert_manager_triggers(monkeypatch):
    thresholds = AlertThresholds(error_rate=0.5, latency_ms=1000, sample_window=4)
    manager = AlertManager(webhook_url="https://hooks.slack.test", thresholds=thresholds)

    async def fake_fetch(*args, **kwargs):
        return [
            {"status": "ERROR", "execution_time_ms": 2000},
            {"status": "ERROR", "execution_time_ms": 1500},
            {"status": "SUCCESS", "execution_time_ms": 500},
            {"status": "SUCCESS", "execution_time_ms": 300},
        ]

    monkeypatch.setattr("services.runtime.src.alerts.db.fetch", fake_fetch)

    class DummyResponse:
        status_code = 200
        text = "ok"

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.payload = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            self.payload = json
            return DummyResponse()

    dummy_client = DummyClient()
    monkeypatch.setattr("httpx.AsyncClient", lambda timeout: dummy_client)
    monkeypatch.setattr("services.runtime.src.alerts.settings", type("Stub", (), {"WEB_APP_URL": "https://app.agentos"})())

    await manager.evaluate(agent_id="agent-1", agent_name="Agent One", telemetry_quality="verified")

    assert dummy_client.payload is not None
    assert "Agent One" in dummy_client.payload["blocks"][0]["text"]["text"]
    button_blocks = [block for block in dummy_client.payload["blocks"] if block.get("type") == "actions"]
    assert button_blocks
    button = button_blocks[0]["elements"][0]
    assert button["url"].startswith("https://app.agentos/logs")
