from pathlib import Path

import pytest
from httpx import AsyncClient

from services.runtime.src.api.agents_v2 import agent_builder
from services.runtime.src.main import app
from services.runtime.src.models_v2 import InvocationStatus
from services.runtime.tests.utils.fake_db import (
    FakeDatabase,
    bootstrap_model_a_agent,
    patch_runtime_db,
)


AGENT_CODE = """
value = input_data.get('value', 0)
if value < 0:
    raise ValueError('negative input')
result = {'result': value * value}
"""


def _extract_trace(payload: dict) -> dict:
    trace = payload.get("metadata", {}).get("trace")
    if trace:
        return trace
    raw = payload.get("metadata", {}).get("raw_execution", {})
    return raw.get("trace", {})


@pytest.mark.asyncio
async def test_model_a_invoke_produces_trace(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer trace-token"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        setup = await bootstrap_model_a_agent(
            client,
            code=AGENT_CODE,
            headers=headers,
        )

        agent_id = setup["agent_id"]
        response = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"value": 9}, "timeout": 5},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == InvocationStatus.SUCCESS.value
    trace = _extract_trace(body)

    assert trace["status"] == InvocationStatus.SUCCESS.value
    assert trace["agent_id"] == agent_id
    assert len(trace["steps"]) >= 1

    step = trace["steps"][0]
    assert step["status"] == InvocationStatus.SUCCESS.value
    exec_time = body["execution_time_ms"]
    latency_diff = abs(exec_time - step["latency_ms"])
    assert latency_diff <= max(5, int(exec_time * 0.05))

    assert step["input_excerpt"].startswith("{")
    assert step["output_excerpt"].startswith("{")


@pytest.mark.asyncio
async def test_model_a_invoke_error_trace(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer trace-token"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        setup = await bootstrap_model_a_agent(
            client,
            code=AGENT_CODE,
            headers=headers,
        )

        agent_id = setup["agent_id"]
        response = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"value": -1}, "timeout": 5},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == InvocationStatus.ERROR.value
    trace = _extract_trace(body)

    assert trace["status"] == InvocationStatus.ERROR.value
    step = trace["steps"][0]
    assert step["status"] == InvocationStatus.ERROR.value
    assert "negative input" in (step.get("error_message") or "")


@pytest.mark.asyncio
async def test_model_a_cost_snapshot_updates(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer cost-token"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        setup = await bootstrap_model_a_agent(
            client,
            code=AGENT_CODE,
            headers=headers,
        )
        agent_id = setup["agent_id"]

        response_success = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"value": 4}, "timeout": 5},
        )
        response_success.raise_for_status()
        cost_success = response_success.json()["cost"]

        response_error = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"value": -2}, "timeout": 5},
        )
        response_error.raise_for_status()
        cost_error = response_error.json()["cost"]

        cost_resp = await client.get(
            f"/v1/agents/{agent_id}/costs",
            headers=headers,
        )
        cost_resp.raise_for_status()

    assert len(fake_db.cost_snapshots) == 1
    snapshot = next(iter(fake_db.cost_snapshots.values()))
    assert snapshot["total_invocations"] == 2
    assert snapshot["successful_invocations"] == 1
    assert snapshot["failed_invocations"] == 1
    expected_total = cost_success + cost_error
    assert snapshot["total_cost"] == pytest.approx(expected_total, rel=1e-6)

    payload = cost_resp.json()
    assert payload["total_cost_usd"] == pytest.approx(expected_total, rel=1e-6)
    assert payload["invocations"] == 2
    assert payload["cost_per_invocation_usd"] == pytest.approx(expected_total / 2, rel=1e-6)
