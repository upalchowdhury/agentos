from pathlib import Path
import uuid

import pytest
from httpx import AsyncClient

from services.runtime.src.api.agents_v2 import agent_builder
from services.runtime.src.main import app
from services.runtime.src.models_v2 import AgentStatus, BuildStatus
from services.runtime.tests.utils.fake_db import (
    FakeDatabase,
    bootstrap_model_a_agent,
    patch_runtime_db,
)


AGENT_CODE = """
value = input_data.get('value', 0)
result = {'result': value * 2}
"""


@pytest.mark.asyncio
async def test_model_a_create_and_artifact_upload(monkeypatch, tmp_path):
    """End-to-end verification of Model A deployment (US-A1)."""

    fake_db = FakeDatabase()
    patch_runtime_db(monkeypatch, fake_db)

    agent_builder._artifacts_dir = Path(tmp_path)
    agent_builder._artifacts_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": "Bearer testtoken123"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        result = await bootstrap_model_a_agent(
            client,
            code=AGENT_CODE,
            headers=headers,
            requirements=["requests==2.32.2"],
        )

    agent_id = result["agent_id"]
    version_id = result["version_id"]
    upload_data = result["upload_response"]
    assert upload_data["status"] == BuildStatus.SUCCESS.value

    agent_uuid = uuid.UUID(agent_id)
    version_uuid = uuid.UUID(version_id)

    agent_entry = fake_db.agents[agent_uuid]
    assert agent_entry["status"] == AgentStatus.RUNNING.value
    assert agent_entry["image_ref"].endswith(f"{agent_id}-{version_id}")
    assert agent_entry["deployed_at"] is not None
    assert agent_entry["metadata"].get("telemetry_quality") == "verified"

    version_entry = fake_db.agent_versions[version_uuid]
    assert version_entry["build_status"] == BuildStatus.SUCCESS.value
    assert version_entry["artifact_checksum"]

    artifact_path = Path(version_entry["artifact_uri"])
    assert artifact_path.exists()
    assert artifact_path.read_text() == AGENT_CODE

    deployment = next(iter(fake_db.agent_deployments.values()))
    assert deployment["metadata"]["version_id"] == version_id
    assert deployment["resource_limits"]["cpu"] == "500m"
