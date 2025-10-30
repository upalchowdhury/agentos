import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional


class FakeRecord(dict):
    """Dictionary that mimics asyncpg.Record access semantics."""

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - defensive
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc


class FakeConnection:
    """Connection façade used inside transaction contexts."""

    def __init__(self, database: "FakeDatabase") -> None:
        self._db = database

    async def execute(self, query: str, *args: Any) -> str:
        return await self._db._execute(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[FakeRecord]:
        return await self._db.fetchrow(query, *args)


class FakeDatabase:
    """
    Minimal in-memory database double that emulates the runtime schema
    for unit tests. It stores rows in dictionaries keyed by UUID.
    """

    def __init__(self) -> None:
        self.agents: Dict[uuid.UUID, Dict[str, Any]] = {}
        self.agent_versions: Dict[uuid.UUID, Dict[str, Any]] = {}
        self.agent_deployments: Dict[uuid.UUID, Dict[str, Any]] = {}
        self.invocations: Dict[uuid.UUID, Dict[str, Any]] = {}
        self.cost_snapshots: Dict[tuple, Dict[str, Any]] = {}

    async def connect(self) -> None:  # pragma: no cover - no-op
        return None

    async def disconnect(self) -> None:  # pragma: no cover - no-op
        return None

    async def execute(self, query: str, *args: Any) -> str:
        return await self._execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[FakeRecord]:  # pragma: no cover - not required yet
        return []

    async def fetchrow(self, query: str, *args: Any) -> Optional[FakeRecord]:
        normalized = " ".join(query.strip().split()).upper()

        if normalized.startswith("SELECT ID, OWNER_ID, MODEL_TYPE FROM AGENTS"):
            agent_id = args[0]
            return self._agent_record(agent_id, fields=["id", "owner_id", "model_type"])

        if "SELECT" in normalized and "FROM AGENTS WHERE ID = $1" in normalized:
            agent_id = args[0]
            return self._agent_record(
                agent_id,
                fields=[
                    "id",
                    "owner_id",
                    "model_type",
                    "status",
                    "runtime",
                    "image_ref",
                    "endpoint_url",
                    "auth_config",
                    "rate_limit_config",
                    "metadata",
                ],
            )

        if normalized.startswith(
            "SELECT ID FROM AGENT_VERSIONS WHERE AGENT_ID = $1 ORDER BY VERSION_NUMBER DESC LIMIT 1"
        ):
            agent_id = args[0]
            versions = [
                FakeRecord({"id": version_id})
                for version_id, payload in self.agent_versions.items()
                if payload["agent_id"] == agent_id
            ]
            if not versions:
                return None
            versions.sort(
                key=lambda record: self.agent_versions[record["id"]]["version_number"],
                reverse=True,
            )
            return versions[0]

        if normalized.startswith(
            "SELECT RESOURCES_JSON, REQUIREMENTS_JSON, ENV_JSON FROM AGENT_VERSIONS WHERE ID = $1"
        ):
            version_id = args[0]
            version = self.agent_versions.get(version_id)
            if not version:
                return None
            return FakeRecord(
                {
                    "resources_json": version["resources"],
                    "requirements_json": version["requirements"],
                    "env_json": version["env"],
                }
            )

        if normalized.startswith(
            "SELECT ID, CODE FROM AGENT_DEPLOYMENTS WHERE AGENT_DID = $1 AND STATUS = $2"
        ):
            agent_did, status = args
            deployments = [
                FakeRecord({"id": deployment_id, "code": payload["code"]})
                for deployment_id, payload in self.agent_deployments.items()
                if payload["agent_did"] == agent_did and payload["status"] == status
            ]
            if not deployments:
                return None
            deployments.sort(
                key=lambda record: self.agent_deployments[record["id"]]["deployed_at"],
                reverse=True,
            )
            return deployments[0]

        if (
            "FROM COST_SNAPSHOTS" in normalized
            and "WHERE AGENT_ID = $1 AND PERIOD_START = $2 AND PERIOD_END = $3" in normalized
        ):
            agent_id, period_start, period_end = args
            key = (agent_id, period_start, period_end)
            snapshot = self.cost_snapshots.get(key)
            if not snapshot:
                return None
            return FakeRecord(snapshot)

        if "FROM COST_SNAPSHOTS" in normalized and "ORDER BY PERIOD_END DESC" in normalized:
            agent_id = args[0]
            entries: List[FakeRecord] = [
                FakeRecord(value)
                for (snap_agent_id, _, _), value in self.cost_snapshots.items()
                if snap_agent_id == agent_id
            ]
            if not entries:
                return None
            entries.sort(key=lambda record: record["period_end"], reverse=True)
            return entries[0]

        raise NotImplementedError(f"Unsupported fetchrow query: {query}")

    @asynccontextmanager
    async def transaction(self):
        yield FakeConnection(self)

    async def _execute(self, query: str, *args: Any) -> str:
        normalized = " ".join(query.strip().split()).upper()

        if normalized.startswith("INSERT INTO AGENTS"):
            agent_id, name, owner_id, model_type, status, runtime, created_at, metadata_json = args
            metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            self.agents[agent_id] = {
                "id": agent_id,
                "name": name,
                "owner_id": owner_id,
                "model_type": model_type,
                "status": status,
                "runtime": runtime,
                "image_ref": None,
                "endpoint_url": None,
                "auth_config": {},
                "rate_limit_config": {},
                "metadata": metadata or {},
                "created_at": created_at,
                "deployed_at": None,
                "updated_at": created_at,
            }
            return "INSERT 0 1"

        if normalized.startswith("INSERT INTO AGENT_VERSIONS"):
            (
                version_id,
                agent_id,
                version_number,
                artifact_uri,
                requirements_json,
                env_json,
                resources_json,
                created_at,
                build_status,
            ) = args
            requirements = json.loads(requirements_json) if isinstance(requirements_json, str) else requirements_json
            env = json.loads(env_json) if isinstance(env_json, str) else env_json
            resources = json.loads(resources_json) if isinstance(resources_json, str) else resources_json
            self.agent_versions[version_id] = {
                "id": version_id,
                "agent_id": agent_id,
                "version_number": version_number,
                "artifact_uri": artifact_uri,
                "requirements": requirements,
                "env": env,
                "resources": resources,
                "build_status": build_status,
                "artifact_checksum": None,
                "artifact_size_bytes": None,
                "build_logs": None,
                "image_ref": None,
                "created_at": created_at,
                "built_at": None,
                "build_error": None,
            }
            return "INSERT 0 1"

        if normalized.startswith("UPDATE AGENT_VERSIONS SET BUILD_STATUS"):
            build_status, build_logs, version_id = args
            version = self.agent_versions[version_id]
            version.update(
                {
                    "build_status": build_status,
                    "build_logs": build_logs,
                }
            )
            return "UPDATE 1"

        if normalized.startswith("UPDATE AGENT_VERSIONS SET ARTIFACT_URI"):
            (
                artifact_uri,
                checksum,
                size_bytes,
                build_status,
                build_logs,
                image_ref,
                built_at,
                version_id,
            ) = args
            version = self.agent_versions[version_id]
            version.update(
                {
                    "artifact_uri": artifact_uri,
                    "artifact_checksum": checksum,
                    "artifact_size_bytes": size_bytes,
                    "build_status": build_status,
                    "build_logs": build_logs,
                    "image_ref": image_ref,
                    "built_at": built_at,
                }
            )
            return "UPDATE 1"

        if normalized.startswith("UPDATE AGENTS SET STATUS = $1 WHERE ID = $2"):
            status, agent_id = args
            agent = self.agents[agent_id]
            agent.update({"status": status, "updated_at": datetime.utcnow()})
            return "UPDATE 1"

        if normalized.startswith("UPDATE AGENTS SET STATUS"):
            status, image_ref, deployed_at, agent_id = args
            agent = self.agents[agent_id]
            agent.update(
                {
                    "status": status,
                    "image_ref": image_ref,
                    "deployed_at": deployed_at,
                    "updated_at": deployed_at,
                }
            )
            return "UPDATE 1"

        if normalized.startswith("UPDATE AGENTS SET STATUS = $1, UPDATED_AT = $2 WHERE ID = $3 AND OWNER_ID = $4"):
            status, updated_at, agent_id, owner_id = args
            agent = self.agents.get(agent_id)
            if not agent or agent["owner_id"] != owner_id:
                return "UPDATE 0"
            agent.update({"status": status, "updated_at": updated_at})
            return "UPDATE 1"

        if normalized.startswith("INSERT INTO AGENT_DEPLOYMENTS"):
            (
                deployment_id,
                agent_did,
                status,
                code,
                code_hash,
                resource_limits_json,
                deployed_at,
                metadata_json,
            ) = args
            resource_limits = (
                json.loads(resource_limits_json) if isinstance(resource_limits_json, str) else resource_limits_json
            )
            metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            self.agent_deployments[deployment_id] = {
                "id": deployment_id,
                "agent_did": agent_did,
                "status": status,
                "code": code,
                "code_hash": code_hash,
                "resource_limits": resource_limits,
                "deployed_at": deployed_at,
                "metadata": metadata,
            }
            return "INSERT 0 1"

        if normalized.startswith("INSERT INTO INVOCATIONS"):
            (
                invocation_id,
                agent_id,
                requester_id,
                caller_agent_id,
                input_data_json,
                output_data_json,
                status,
                started_at,
                ended_at,
                execution_time_ms,
                cost_decimal,
                metadata_json,
            ) = args
            self.invocations[invocation_id] = {
                "agent_id": agent_id,
                "requester_id": requester_id,
                "caller_agent_id": caller_agent_id,
                "input_data": json.loads(input_data_json),
                "output_data": json.loads(output_data_json) if output_data_json else None,
                "status": status,
                "started_at": started_at,
                "ended_at": ended_at,
                "execution_time_ms": execution_time_ms,
                "cost_decimal": cost_decimal,
                "metadata": json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json,
            }
            return "INSERT 0 1"

        if normalized.startswith("UPDATE COST_SNAPSHOTS SET TOTAL_INVOCATIONS"):
            (
                total_invocations,
                successful_invocations,
                failed_invocations,
                total_cost,
                compute_cost,
                llm_api_cost,
                storage_cost,
                agent_id,
                period_start,
                period_end,
            ) = args
            key = (agent_id, period_start, period_end)
            snapshot = self.cost_snapshots[key]
            snapshot.update(
                {
                    "total_invocations": total_invocations,
                    "successful_invocations": successful_invocations,
                    "failed_invocations": failed_invocations,
                    "total_cost": float(total_cost),
                    "compute_cost": float(compute_cost),
                    "llm_api_cost": float(llm_api_cost),
                    "storage_cost": float(storage_cost),
                }
            )
            return "UPDATE 1"

        if normalized.startswith("INSERT INTO COST_SNAPSHOTS"):
            (
                snapshot_id,
                agent_id,
                owner_id,
                period_start,
                period_end,
                total_invocations,
                successful_invocations,
                failed_invocations,
                total_cost,
                compute_cost,
                llm_api_cost,
                storage_cost,
                created_at,
            ) = args
            key = (agent_id, period_start, period_end)
            self.cost_snapshots[key] = {
                "id": snapshot_id,
                "agent_id": agent_id,
                "owner_id": owner_id,
                "period_start": period_start,
                "period_end": period_end,
                "total_invocations": total_invocations,
                "successful_invocations": successful_invocations,
                "failed_invocations": failed_invocations,
                "total_cost": float(total_cost),
                "compute_cost": float(compute_cost),
                "llm_api_cost": float(llm_api_cost),
                "storage_cost": float(storage_cost),
                "created_at": created_at,
            }
            return "INSERT 0 1"

        raise NotImplementedError(f"Unsupported execute query: {query}")

    def _agent_record(self, agent_id: uuid.UUID, fields: List[str]) -> Optional[FakeRecord]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        record = {field: agent.get(field) for field in fields}
        return FakeRecord(record)


def patch_runtime_db(monkeypatch, fake_db: FakeDatabase) -> None:
    """Patch all runtime modules to use the provided fake database."""
    monkeypatch.setattr("services.runtime.src.database.db", fake_db, raising=False)
    monkeypatch.setattr("services.runtime.src.api.agents_v2.db", fake_db, raising=False)
    monkeypatch.setattr("services.runtime.src.agents.builder.db", fake_db, raising=False)


async def bootstrap_model_a_agent(
    client,
    code: str,
    headers: Dict[str, str],
    name: str = "demo-agent",
    requirements: Optional[List[str]] = None,
    resources: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Helper that creates a Model A agent and uploads its artifact.

    Returns metadata containing agent_id, version_id, and request payloads.
    """
    payload = {
        "name": name,
        "runtime": "python3.11",
        "requirements": requirements or [],
        "env": {"API_KEY": "secret"},
        "resources": resources or {"cpu": "500m", "mem": "512Mi"},
    }

    create_response = await client.post("/v1/agents/modelA", json=payload, headers=headers)
    create_response.raise_for_status()
    create_data = create_response.json()

    agent_id = create_data["agent_id"]
    version_id = create_data["deployment_id"]

    files = {"file": ("agent.py", code.encode("utf-8"), "text/x-python")}
    upload_response = await client.put(f"/v1/agents/{agent_id}/artifact", headers=headers, files=files)
    upload_response.raise_for_status()

    return {
        "agent_id": agent_id,
        "version_id": version_id,
        "create_payload": payload,
        "create_response": create_data,
        "upload_response": upload_response.json(),
        "code": code,
    }
