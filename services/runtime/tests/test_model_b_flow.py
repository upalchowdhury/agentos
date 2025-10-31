import asyncio
from pathlib import Path

import pytest
from httpx import AsyncClient

from services.runtime.src.main import app
from services.runtime.src.models_v2 import ModelType, InvocationStatus
from services.runtime.tests.utils.fake_db import FakeDatabase, patch_runtime_db


@pytest.mark.asyncio
async def test_model_b_registration_health(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    async def fake_health(self, health_path="/health"):
        return True

    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.health_check",
        fake_health,
        raising=False,
    )

    headers = {"Authorization": "Bearer registry-token"}
    payload = {
        "name": "external-agent",
        "endpoint_url": "https://example.com/agent",
        "auth": {"type": "bearer", "value": "token"},
        "rate_limit": {"rps": 2, "burst": 5},
        "health_check_path": "/custom-health",
        "timeout_seconds": 15,
    }

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post("/v1/agents/modelB", json=payload, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["health_status"] == "healthy"
    assert body["telemetry_quality"] == "partial"

    # Verify persistence
    assert len(fake_db.agents) == 1
    agent_record = next(iter(fake_db.agents.values()))
    assert agent_record["model_type"] == ModelType.B.value
    assert agent_record["health_status"] == "healthy"
    assert agent_record["metadata"]["health_check_path"] == "/custom-health"
    assert agent_record["metadata"]["rate_limit"]["rps"] == 2
    assert agent_record["metadata"].get("telemetry_quality") == "partial"


@pytest.mark.asyncio
async def test_model_b_rate_limit_enforced(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    async def fake_health(self, health_path="/health"):
        return True

    async def fake_invoke(self, input_data, timeout=None):
        await asyncio.sleep(0.01)
        return {"result": {"ok": True}, "metadata": {}, "cost": 0.0}

    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.health_check",
        fake_health,
        raising=False,
    )
    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.invoke",
        fake_invoke,
        raising=False,
    )

    call_count = 0

    async def fake_rate_try(agent_id, rps, burst):
        nonlocal call_count
        call_count += 1
        return call_count == 1

    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.rate_limit_manager.try_acquire",
        fake_rate_try,
    )

    headers = {"Authorization": "Bearer registry-token"}
    payload = {
        "name": "external-agent",
        "endpoint_url": "https://example.com/agent",
        "auth": {"type": "bearer", "value": "token"},
        "rate_limit": {"rps": 1, "burst": 1},
    }

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        register = await client.post("/v1/agents/modelB", json=payload, headers=headers)
        agent_id = register.json()["agent_id"]

        first = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"q": "hello"}},
        )

        second = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"q": "again"}},
        )

    assert first.status_code == 200
    assert first.json()["status"] == "SUCCESS"

    assert second.status_code == 429
    assert "limit" in second.json()["detail"].lower()

    snapshot = next(iter(fake_db.cost_snapshots.values()))
    assert snapshot["total_invocations"] == 2
    assert snapshot["successful_invocations"] == 1
    assert snapshot["failed_invocations"] == 1


@pytest.mark.asyncio
async def test_model_b_partial_telemetry(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    async def fake_health(self, health_path="/health"):
        return True

    async def fake_invoke(self, input_data, timeout=None):
        return {"result": {"answer": 42}, "metadata": {}, "cost": 0.0}

    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.health_check",
        fake_health,
        raising=False,
    )
    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.invoke",
        fake_invoke,
        raising=False,
    )

    headers = {"Authorization": "Bearer telemetry-token"}
    payload = {
        "name": "external-agent",
        "endpoint_url": "https://example.com/agent",
        "auth": {"type": "bearer", "value": "token"},
    }

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        register = await client.post("/v1/agents/modelB", json=payload, headers=headers)
        agent_id = register.json()["agent_id"]

        invoke = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"ping": True}},
        )

    assert invoke.status_code == 200
    body = invoke.json()
    assert body["status"] == InvocationStatus.SUCCESS.value
    assert body["metadata"]["telemetry_quality"] == "partial"
    trace = body["metadata"].get("trace")
    assert trace
    assert trace["status"] == InvocationStatus.SUCCESS.value


@pytest.mark.asyncio
async def test_model_b_verified_telemetry(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    async def fake_health(self, health_path="/health"):
        return True

    def build_trace():
        return {
            "trace_id": "trace-123",
            "status": InvocationStatus.SUCCESS.value,
            "steps": [
                {
                    "step_id": "step-1",
                    "status": InvocationStatus.SUCCESS.value,
                    "start_ts": None,
                    "end_ts": None,
                    "latency_ms": 10,
                }
            ],
        }

    async def fake_invoke(self, input_data, timeout=None):
        return {
            "result": {"answer": 42, "telemetry": {"trace": build_trace()}},
            "metadata": {
                "telemetry_quality": "verified",
                "trace": build_trace(),
            },
            "cost": 0.0,
        }

    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.health_check",
        fake_health,
        raising=False,
    )
    monkeypatch.setattr(
        "services.runtime.src.api.agents_v2.ExternalAgentProxy.invoke",
        fake_invoke,
        raising=False,
    )

    headers = {"Authorization": "Bearer telemetry-token"}
    payload = {
        "name": "external-agent",
        "endpoint_url": "https://example.com/agent",
        "auth": {"type": "bearer", "value": "token"},
    }

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        register = await client.post("/v1/agents/modelB", json=payload, headers=headers)
        agent_id = register.json()["agent_id"]

        invoke = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"ping": True}},
        )
        agent_details = await client.get(
            f"/v1/agents/{agent_id}",
            headers=headers,
        )

    assert invoke.status_code == 200
    body = invoke.json()
    assert body["metadata"]["telemetry_quality"] == "verified"
    assert body["metadata"]["trace"]["status"] == InvocationStatus.SUCCESS.value

    agent_record = next(iter(fake_db.agents.values()))
    assert agent_record["metadata"].get("telemetry_quality") == "verified"

    assert agent_details.status_code == 200
    assert agent_details.json()["telemetry_quality"] == "verified"
