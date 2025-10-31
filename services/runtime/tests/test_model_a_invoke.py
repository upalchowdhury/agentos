import asyncio
import json
from pathlib import Path

import pytest
from httpx import AsyncClient

from services.runtime.src.api.agents_v2 import agent_builder
from services.runtime.src.main import app
from services.runtime.src.models_v2 import InvocationStatus
from services.runtime.src.opa_client import enforce_obligations
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

CONCURRENCY_CODE = """
import time
time.sleep(0.2)
result = {'ok': True}
"""

PII_CODE = """
email = input_data.get('customer_email', '')
result = {
    'echo': f'Captured email: {email}',
    'details': {'ssn': '123-45-6789'}
}
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
    actor = body["metadata"].get("actor", {})
    assert actor.get("requester_id", "").startswith("user_")
    assert actor.get("caller_agent_id") is None
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
    actor = body["metadata"].get("actor", {})
    assert actor.get("requester_id", "").startswith("user_")
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

    expected_total = cost_success + cost_error
    assert len(fake_db.cost_snapshots) == 1
    snapshot = next(iter(fake_db.cost_snapshots.values()))
    assert snapshot["total_invocations"] == 2
    assert snapshot["successful_invocations"] == 1
    assert snapshot["failed_invocations"] == 1

    payload = cost_resp.json()
    assert payload["total_cost_usd"] == pytest.approx(expected_total, rel=1e-6)
    assert payload["invocations"] == 2
    assert payload["cost_per_invocation_usd"] == pytest.approx(expected_total / 2, rel=1e-6)


@pytest.mark.asyncio
async def test_model_a_invocation_alerts_trigger(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer alert-token"}

    from services.runtime.src.api import agents_v2  # Imported lazily for monkeypatch compatibility

    class DummyAlert:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        async def evaluate(self, **kwargs):
            self.calls.append(kwargs)

    dummy = DummyAlert()
    monkeypatch.setattr(agents_v2, "alert_manager", dummy)

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
            json={"input_data": {"value": 4}, "timeout": 5},
        )

    assert response.status_code == 200
    assert dummy.calls
    call = dummy.calls[0]
    assert call["agent_id"] == agent_id
    assert call["agent_name"]


@pytest.mark.asyncio
async def test_model_a_invocation_obligations_apply_pii_redaction(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer pii-token"}

    from services.runtime.src.api import agents_v2  # Imported lazily for monkeypatch compatibility

    class StubOPA:
        def __init__(self) -> None:
            self.obligations = {"pii_redaction": True, "content_filter": True, "audit_log": True}

        async def check_invoke_permission(self, *args, **kwargs):
            return {"allow": True, "obligations": self.obligations}

        async def apply_obligations(
            self,
            obligations,
            *,
            input_data=None,
            output_data=None,
            metadata=None,
        ):
            return enforce_obligations(
                obligations,
                input_data=input_data,
                output_data=output_data,
                metadata=metadata,
            )

    monkeypatch.setattr(agents_v2, "opa_client", StubOPA())

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        setup = await bootstrap_model_a_agent(
            client,
            code=PII_CODE,
            headers=headers,
        )

        agent_id = setup["agent_id"]
        response = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={
                "input_data": {"customer_email": "john.doe@example.com"},
                "timeout": 5,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    actor = payload["metadata"]["actor"]
    assert actor["requester_id"].startswith("user_")
    assert actor["caller_agent_id"] is None
    payload_repr = json.dumps(payload)
    assert "[REDACTED:EMAIL]" in payload_repr
    assert "john.doe@example.com" not in payload_repr
    assert "123-45-6789" not in payload_repr

    enforcement = payload["metadata"]["policy"]["enforcement"]["pii_redaction"]
    assert enforcement["total_matches"] >= 2

    invocation_record = next(iter(fake_db.invocations.values()))
    record_repr = json.dumps(invocation_record, default=str)
    assert "[REDACTED:EMAIL]" in record_repr
    assert "john.doe@example.com" not in record_repr
    assert "123-45-6789" not in record_repr

    stored_input = invocation_record["input_data"]
    assert stored_input["customer_email"].startswith("[REDACTED:EMAIL]")

    trace = invocation_record["metadata"].get("trace", {})
    steps = trace.get("steps", [])
    if steps:
        excerpt = steps[0].get("input_excerpt") or ""
        assert "john.doe@example.com" not in excerpt
        assert "[REDACTED:EMAIL]" in excerpt

    policy_info = invocation_record["metadata"]["policy"]
    assert policy_info["obligations"]["pii_redaction"] is True
    assert policy_info["enforcement"]["pii_redaction"]["total_matches"] >= 2


@pytest.mark.asyncio
async def test_model_a_concurrency_limit_enforced(monkeypatch, tmp_path):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer concurrency-token"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        setup = await bootstrap_model_a_agent(
            client,
            code=CONCURRENCY_CODE,
            headers=headers,
            concurrency_limit=1,
        )

        agent_id = setup["agent_id"]

        first_task = asyncio.create_task(
            client.post(
                f"/v1/agents/{agent_id}/invoke",
                headers=headers,
                json={"input_data": {"value": 1}, "timeout": 5},
            )
        )

        await asyncio.sleep(0.05)

        second_response = await client.post(
            f"/v1/agents/{agent_id}/invoke",
            headers=headers,
            json={"input_data": {"value": 2}, "timeout": 5},
        )

        first_response = await first_task

    assert first_response.status_code == 200
    assert first_response.json()["status"] == InvocationStatus.SUCCESS.value

    assert second_response.status_code == 200
    second_body = second_response.json()
    assert second_body["status"] == InvocationStatus.ERROR.value
    assert "Concurrency limit" in (second_body.get("error") or "")
    assert second_body["metadata"]["actor"]["requester_id"].startswith("user_")

    snapshot = next(iter(fake_db.cost_snapshots.values()))
    assert snapshot["total_invocations"] == 2
    assert snapshot["successful_invocations"] == 1
    assert snapshot["failed_invocations"] == 1
