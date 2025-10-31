import csv
import io
from datetime import datetime, timedelta
import uuid

import pytest
from httpx import AsyncClient

from services.runtime.src.main import app
from services.runtime.tests.utils.fake_db import FakeDatabase, patch_runtime_db


@pytest.mark.asyncio
async def test_observability_agents_with_data(monkeypatch):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)
    monkeypatch.setattr("services.runtime.src.api.observability.db", fake_db, raising=False)

    token = "user_token_value"
    owner_id = f"user_{token[:8]}"

    agent_id = uuid.uuid4()
    fake_db.agents[agent_id] = {
        "id": agent_id,
        "name": "demo-agent",
        "owner_id": owner_id,
        "model_type": "A",
        "status": "RUNNING",
        "runtime": "python3.11",
        "image_ref": None,
        "endpoint_url": None,
        "auth_config": {},
        "rate_limit_config": {},
        "metadata": {"telemetry_quality": "verified"},
        "created_at": datetime.utcnow(),
        "deployed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "health_status": None,
        "health_checked_at": None,
    }

    inv_id = uuid.uuid4()
    fake_db.invocations[inv_id] = {
        "agent_id": agent_id,
        "requester_id": owner_id,
        "caller_agent_id": None,
        "input_data": {},
        "output_data": {},
        "status": "SUCCESS",
        "started_at": datetime.utcnow() - timedelta(minutes=10),
        "ended_at": datetime.utcnow() - timedelta(minutes=10, seconds=-1),
        "execution_time_ms": 120,
        "cost_decimal": 0.02,
        "metadata": {"policy_alerts": {"pii": {}}},
    }

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/v1/observability/agents", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    summary = data[0]
    assert summary["agent_id"] == str(agent_id)
    assert summary["name"] == "demo-agent"
    assert summary["telemetry_quality"] == "verified"
    assert summary["total_invocations"] == 1
    assert summary["success_rate"] == pytest.approx(1.0)
    assert summary["p95_latency_ms"] == 120
    assert summary["cost_usd"] == pytest.approx(0.02)
    assert summary["denied_invocations"] == 0
    assert summary["policy_alerts_count"] == 1


@pytest.mark.asyncio
async def test_observability_returns_empty_without_agents(monkeypatch):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)
    monkeypatch.setattr("services.runtime.src.api.observability.db", fake_db, raising=False)

    token = "none_token"
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/v1/observability/agents", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_observability_recent_invocations(monkeypatch):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)
    monkeypatch.setattr("services.runtime.src.api.observability.db", fake_db, raising=False)

    token = "trace_token"
    owner_id = f"user_{token[:8]}"
    agent_id = uuid.uuid4()

    fake_db.agents[agent_id] = {
        "id": agent_id,
        "name": "trace-agent",
        "owner_id": owner_id,
        "model_type": "B",
        "status": "RUNNING",
        "runtime": None,
        "image_ref": None,
        "endpoint_url": "https://example.com",
        "auth_config": {},
        "rate_limit_config": {},
        "metadata": {"telemetry_quality": "partial"},
        "created_at": datetime.utcnow(),
        "deployed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "health_status": "healthy",
        "health_checked_at": datetime.utcnow(),
    }

    inv_id = uuid.uuid4()
    fake_db.invocations[inv_id] = {
        "id": inv_id,
        "agent_id": agent_id,
        "requester_id": owner_id,
        "caller_agent_id": None,
        "input_data": {},
        "output_data": {},
        "status": "SUCCESS",
        "started_at": datetime.utcnow(),
        "ended_at": datetime.utcnow(),
        "execution_time_ms": 200,
        "cost_decimal": 0.1,
        "metadata": {
            "trace": {"trace_id": "abc123"},
            "telemetry_quality": "verified",
            "actor": {
                "requester_id": owner_id,
                "caller_agent_id": None,
                "subject_type": "user",
            },
            "policy": {
                "obligations": {"pii_redaction": True},
                "enforcement": {"pii_redaction": {"total_matches": 1}},
            },
            "policy_alerts": {
                "content_filter": {"flagged": [{"path": "$.input", "type": "credential_leak"}]}
            },
            "logs": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "message": "Execution completed",
                    "trace_id": "abc123",
                    "actor": {
                        "requester_id": owner_id,
                        "caller_agent_id": None,
                        "subject_type": "user",
                    },
                    "policy_alerts": {
                        "content_filter": {"flagged": [{"path": "$.input", "type": "credential_leak"}]}
                    },
                }
            ],
        },
    }

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/v1/observability/agents/invocations", headers=headers)

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    entry = items[0]
    assert entry["agent_id"] == str(agent_id)
    assert entry["telemetry_quality"] == "verified"
    assert entry["trace_id"] == "abc123"
    assert entry["requester_id"] == owner_id
    assert entry["caller_agent_id"] is None
    assert entry["actor"]["subject_type"] == "user"

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        filtered = await client.get(
            "/v1/observability/agents/invocations",
            headers=headers,
            params={"query": "trace-agent"},
        )

    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        trace_response = await client.get(
            f"/v1/observability/agents/trace/{inv_id}",
            headers=headers,
        )

    assert trace_response.status_code == 200
    trace_payload = trace_response.json()
    assert trace_payload["invocation_id"] == str(inv_id)
    assert trace_payload["telemetry_quality"] == "verified"
    assert trace_payload["trace_id"]
    assert isinstance(trace_payload["steps"], list)
    assert trace_payload["requester_id"] == owner_id
    assert trace_payload["caller_agent_id"] is None
    assert trace_payload["actor"]["subject_type"] == "user"
    assert trace_payload["policy"]["obligations"]["pii_redaction"] is True
    assert trace_payload["policy"]["enforcement"]["pii_redaction"]["total_matches"] == 1
    assert "content_filter" in trace_payload.get("policy_alerts", {})

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        logs_response = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"trace_id": "abc123"},
        )

    assert logs_response.status_code == 200
    logs_data = logs_response.json()
    assert len(logs_data) >= 1
    first_log = logs_data[0]
    assert first_log["trace_id"] == "abc123"
    assert first_log["requester_id"] == owner_id
    assert first_log["caller_agent_id"] is None
    assert "content_filter" in first_log.get("policy_alerts", {})


@pytest.mark.asyncio
async def test_observability_logs_filtering(monkeypatch):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)
    monkeypatch.setattr("services.runtime.src.api.observability.db", fake_db, raising=False)

    token = "log_token"
    owner_id = f"user_{token[:8]}"
    headers = {"Authorization": f"Bearer {token}"}

    agent_a = uuid.uuid4()
    agent_b = uuid.uuid4()

    now = datetime.utcnow()

    fake_db.agents[agent_a] = {
        "id": agent_a,
        "name": "alpha-agent",
        "owner_id": owner_id,
        "model_type": "A",
        "status": "RUNNING",
        "runtime": "python3.11",
        "image_ref": None,
        "endpoint_url": None,
        "auth_config": {},
        "rate_limit_config": {},
        "metadata": {},
        "created_at": now,
        "deployed_at": now,
        "updated_at": now,
        "health_status": None,
        "health_checked_at": None,
    }

    fake_db.agents[agent_b] = {
        "id": agent_b,
        "name": "beta-agent",
        "owner_id": owner_id,
        "model_type": "B",
        "status": "RUNNING",
        "runtime": None,
        "image_ref": None,
        "endpoint_url": "https://example.org",
        "auth_config": {},
        "rate_limit_config": {},
        "metadata": {},
        "created_at": now,
        "deployed_at": now,
        "updated_at": now,
        "health_status": "healthy",
        "health_checked_at": now,
    }

    inv_a = uuid.uuid4()
    inv_b = uuid.uuid4()

    fake_db.invocations[inv_a] = {
        "id": inv_a,
        "agent_id": agent_a,
        "requester_id": owner_id,
        "caller_agent_id": None,
        "input_data": {},
        "output_data": {},
        "status": "SUCCESS",
        "started_at": now - timedelta(minutes=5),
        "ended_at": now - timedelta(minutes=5, seconds=-1),
        "execution_time_ms": 180,
        "cost_decimal": 0.05,
        "metadata": {
            "trace": {"trace_id": "trace-alpha"},
            "actor": {
                "requester_id": owner_id,
                "caller_agent_id": None,
                "subject_type": "user",
            },
            "policy": {
                "obligations": {"audit_log": True},
                "enforcement": {},
            },
            "logs": [
                {
                    "timestamp": now.isoformat(),
                    "level": "INFO",
                    "message": "Alpha completed",
                    "trace_id": "trace-alpha",
                    "actor": {
                        "requester_id": owner_id,
                        "caller_agent_id": None,
                        "subject_type": "user",
                    },
                    "policy_alerts": {},
                }
            ],
        },
    }

    caller_agent = "agent-ext-99"
    fake_db.invocations[inv_b] = {
        "id": inv_b,
        "agent_id": agent_b,
        "requester_id": owner_id,
        "caller_agent_id": caller_agent,
        "input_data": {},
        "output_data": {},
        "status": "ERROR",
        "started_at": now - timedelta(minutes=3),
        "ended_at": now - timedelta(minutes=3, seconds=-1),
        "execution_time_ms": 220,
        "cost_decimal": 0.08,
        "metadata": {
            "trace": {"trace_id": "trace-beta"},
            "actor": {
                "requester_id": owner_id,
                "caller_agent_id": caller_agent,
                "subject_type": "agent",
            },
            "policy": {
                "obligations": {"pii_redaction": True},
                "enforcement": {"pii_redaction": {"total_matches": 2}},
            },
            "policy_alerts": {
                "content_filter": {"flagged": [{"path": "$.metadata"}]},
            },
            "logs": [
                {
                    "timestamp": now.isoformat(),
                    "level": "ERROR",
                    "message": "Beta failed",
                    "trace_id": "trace-beta",
                    "actor": {
                        "requester_id": owner_id,
                        "caller_agent_id": caller_agent,
                        "subject_type": "agent",
                    },
                    "policy_alerts": {
                        "content_filter": {"flagged": [{"path": "$.metadata"}]}
                    },
                }
            ],
        },
    }

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        all_logs_resp = await client.get("/v1/observability/logs", headers=headers)
        assert all_logs_resp.status_code == 200
        all_logs = all_logs_resp.json()
        assert len(all_logs) == 2

        trace_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"trace_id": "trace-alpha"},
        )
        assert trace_filtered.status_code == 200
        trace_payload = trace_filtered.json()
        assert len(trace_payload) == 1
        assert trace_payload[0]["trace_id"] == "trace-alpha"
        assert trace_payload[0]["agent_id"] == str(agent_a)
        assert trace_payload[0]["requester_id"] == owner_id

        agent_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"agent_id": str(agent_b)},
        )
        assert agent_filtered.status_code == 200
        agent_payload = agent_filtered.json()
        assert len(agent_payload) == 1
        assert agent_payload[0]["agent_id"] == str(agent_b)
        assert agent_payload[0]["trace_id"] == "trace-beta"
        assert agent_payload[0]["caller_agent_id"] == caller_agent

        combo_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"trace_id": "trace-beta", "agent_id": str(agent_b)},
        )
        assert combo_filtered.status_code == 200
        combo_payload = combo_filtered.json()
        assert len(combo_payload) == 1
        assert combo_payload[0]["trace_id"] == "trace-beta"
        assert combo_payload[0]["agent_id"] == str(agent_b)
        assert combo_payload[0]["caller_agent_id"] == caller_agent

        level_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"level": "ERROR"},
        )
        assert level_filtered.status_code == 200
        level_payload = level_filtered.json()
        assert len(level_payload) == 1
        assert level_payload[0]["trace_id"] == "trace-beta"

        subject_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"subject_type": "agent"},
        )
        assert subject_filtered.status_code == 200
        subject_payload = subject_filtered.json()
        assert len(subject_payload) == 1
        assert subject_payload[0]["subject_type"] == "agent"

        requester_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"requester_id": owner_id},
        )
        assert requester_filtered.status_code == 200
        requester_payload = requester_filtered.json()
        assert len(requester_payload) == 2

        caller_filtered = await client.get(
            "/v1/observability/logs",
            headers=headers,
            params={"caller_agent_id": caller_agent},
        )
        assert caller_filtered.status_code == 200
        caller_payload = caller_filtered.json()
        assert len(caller_payload) == 1
        assert caller_payload[0]["caller_agent_id"] == caller_agent


@pytest.mark.asyncio
async def test_observability_audit_export(monkeypatch):
    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)
    monkeypatch.setattr("services.runtime.src.api.observability.db", fake_db, raising=False)

    token = "audit_token"
    owner_id = f"user_{token[:8]}"
    agent_id = uuid.uuid4()

    fake_db.agents[agent_id] = {
        "id": agent_id,
        "name": "audit-agent",
        "owner_id": owner_id,
        "model_type": "A",
        "status": "RUNNING",
        "runtime": "python3.11",
        "image_ref": None,
        "endpoint_url": None,
        "auth_config": {},
        "rate_limit_config": {},
        "metadata": {},
        "created_at": datetime.utcnow(),
        "deployed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "health_status": None,
        "health_checked_at": None,
    }

    now = datetime.utcnow()

    success_id = uuid.uuid4()
    fake_db.invocations[success_id] = {
        "id": success_id,
        "agent_id": agent_id,
        "requester_id": owner_id,
        "caller_agent_id": None,
        "input_data": {},
        "output_data": {},
        "status": "SUCCESS",
        "started_at": now - timedelta(minutes=5),
        "ended_at": now - timedelta(minutes=5, seconds=-10),
        "execution_time_ms": 150,
        "cost_decimal": 0.05,
        "metadata": {
            "actor": {
                "requester_id": owner_id,
                "subject_type": "user",
            },
            "policy": {
                "obligations": {"pii_redaction": True},
            },
            "policy_alerts": {
                "content_filter": {"flagged": []},
            },
        },
    }

    denied_id = uuid.uuid4()
    fake_db.invocations[denied_id] = {
        "id": denied_id,
        "agent_id": agent_id,
        "requester_id": owner_id,
        "caller_agent_id": "external-agent",
        "input_data": {},
        "output_data": {},
        "status": "DENIED",
        "started_at": now - timedelta(minutes=2),
        "ended_at": now - timedelta(minutes=2),
        "execution_time_ms": 0,
        "cost_decimal": 0.0,
        "metadata": {
            "actor": {
                "requester_id": owner_id,
                "caller_agent_id": "external-agent",
                "subject_type": "agent",
            },
            "policy_alerts": {
                "domain_block": {"flagged": [{"path": "$.output"}]},
            },
        },
    }

    headers = {"Authorization": f"Bearer {token}"}
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(minutes=1)).isoformat()

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/v1/observability/audit/export",
            headers=headers,
            params={"start": start, "end": end, "limit": 10},
        )

    assert response.status_code == 200
    csv_bytes = response.content
    reader = csv.reader(io.StringIO(csv_bytes.decode("utf-8")))
    rows = list(reader)
    assert rows[0] == [
        "invocation_id",
        "agent_id",
        "agent_name",
        "status",
        "requester_id",
        "caller_agent_id",
        "subject_type",
        "started_at",
        "ended_at",
        "execution_time_ms",
        "cost_usd",
        "policy_alerts",
        "policy_obligations",
    ]
    assert len(rows) == 3
    statuses = {row[3] for row in rows[1:]}
    assert statuses == {"SUCCESS", "DENIED"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        denied_only = await client.get(
            "/v1/observability/audit/export",
            headers=headers,
            params={"start": start, "end": end, "status": "DENIED"},
        )

    assert denied_only.status_code == 200
    denied_rows = list(csv.reader(io.StringIO(denied_only.content.decode("utf-8"))))
    assert len(denied_rows) == 2
    assert all(row[3] == "DENIED" for row in denied_rows[1:])
