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
        normalized = " ".join(query.strip().split()).upper()

        if normalized.startswith("SELECT ID, NAME, METADATA, MODEL_TYPE, RUNTIME FROM AGENTS WHERE OWNER_ID = $1"):
            owner_id = args[0]
            results = [
                FakeRecord({
                    "id": agent_id,
                    "name": agent["name"],
                    "metadata": agent.get("metadata", {}),
                    "model_type": agent.get("model_type"),
                    "runtime": agent.get("runtime"),
                })
                for agent_id, agent in self.agents.items()
                if agent.get("owner_id") == owner_id
            ]
            return results

        if normalized.startswith("SELECT AGENT_ID, STATUS, EXECUTION_TIME_MS, COST_DECIMAL, METADATA FROM INVOCATIONS"):
            threshold = args[0]
            rows: List[FakeRecord] = []
            for record in self.invocations.values():
                if record["started_at"] >= threshold:
                    rows.append(
                        FakeRecord({
                            "agent_id": record["agent_id"],
                            "status": record["status"],
                            "execution_time_ms": record.get("execution_time_ms"),
                            "cost_decimal": record.get("cost_decimal"),
                            "metadata": record.get("metadata"),
                            "started_at": record["started_at"],
                        })
                    )
            return rows

        if normalized.startswith("SELECT I.ID, I.AGENT_ID, A.NAME AS AGENT_NAME") and "FROM INVOCATIONS I" in normalized:
            user_id = args[0]
            start_at = args[1]
            end_at = args[2]
            extras = list(args[3:-1])
            limit = args[-1]

            agent_filter = None
            status_filter = None
            for value in extras:
                if isinstance(value, uuid.UUID):
                    agent_filter = value
                elif isinstance(value, str):
                    status_filter = value

            matching: List[FakeRecord] = []
            for record in sorted(self.invocations.values(), key=lambda r: r["started_at"], reverse=True):
                agent = self.agents.get(record["agent_id"])
                if not agent or agent.get("owner_id") != user_id:
                    continue
                if record["started_at"] < start_at or record["started_at"] > end_at:
                    continue
                if agent_filter and record["agent_id"] != agent_filter:
                    continue
                if status_filter and record.get("status") != status_filter:
                    continue

                metadata = record.get("metadata")
                if isinstance(metadata, dict):
                    metadata_copy = dict(metadata)
                else:
                    metadata_copy = metadata

                matching.append(
                    FakeRecord({
                        "id": record.get("id") or uuid.uuid4(),
                        "agent_id": record["agent_id"],
                        "agent_name": agent.get("name"),
                        "requester_id": record.get("requester_id"),
                        "caller_agent_id": record.get("caller_agent_id"),
                        "status": record.get("status"),
                        "started_at": record.get("started_at"),
                        "ended_at": record.get("ended_at"),
                        "execution_time_ms": record.get("execution_time_ms"),
                        "cost_decimal": record.get("cost_decimal"),
                        "metadata": metadata_copy,
                    })
                )
                if len(matching) >= limit:
                    break
            return matching

        if "JOIN AGENTS" in normalized and "FROM INVOCATIONS" in normalized:
            owner_id = args[0]
            pattern = None
            limit = None
            if "LIKE" in normalized and len(args) >= 3:
                pattern = args[1].replace('%', '').lower()
                limit = args[2]
            elif len(args) >= 2:
                limit = args[1]
            else:
                limit = 200
            rows: List[FakeRecord] = []
            for record in sorted(self.invocations.values(), key=lambda r: r["started_at"], reverse=True):
                agent = self.agents.get(record["agent_id"])
                if not agent or agent.get("owner_id") != owner_id:
                    continue
                if pattern and pattern not in agent.get("name", "").lower() and pattern not in str(record.get("id", "")).lower() and pattern not in str(record.get("agent_id", "")).lower():
                    continue
                metadata = record.get("metadata") or {}
                if isinstance(metadata, dict):
                    metadata_copy = dict(metadata)
                else:
                    metadata_copy = metadata
                rows.append(
                    FakeRecord({
                        "id": record.get("id") or uuid.uuid4(),
                        "agent_id": record["agent_id"],
                        "status": record["status"],
                        "started_at": record["started_at"],
                        "execution_time_ms": record.get("execution_time_ms"),
                        "metadata": metadata_copy,
                        "requester_id": record.get("requester_id"),
                        "caller_agent_id": record.get("caller_agent_id"),
                        "name": agent.get("name"),
                        "agent_metadata": agent.get("metadata"),
                    })
                )
                if limit is not None and len(rows) >= limit:
                    break
            return rows

        if normalized.startswith("SELECT STATUS, EXECUTION_TIME_MS FROM INVOCATIONS WHERE AGENT_ID = $1"):
            agent_id = args[0]
            limit = args[1]
            records = [
                FakeRecord({
                    "status": record["status"],
                    "execution_time_ms": record.get("execution_time_ms")
                })
                for record in sorted(self.invocations.values(), key=lambda r: r["started_at"], reverse=True)
                if record["agent_id"] == agent_id
            ]
            return records[:limit]

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

        if "COUNT(I.ID)" in normalized and "FROM AGENTS" in normalized:
            agent_id, owner_id = args
            agent = self.agents.get(agent_id)
            if not agent or agent.get("owner_id") != owner_id:
                return None

            invocations = [
                record
                for record in self.invocations.values()
                if record["agent_id"] == agent_id
            ]

            invocation_count = len(invocations)
            cost_to_date = sum(record["cost_decimal"] or 0.0 for record in invocations)

            return FakeRecord(
                {
                    **agent,
                    "invocation_count": invocation_count,
                    "cost_to_date": cost_to_date,
                }
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

        if (
            "SELECT I.*, A.NAME AS AGENT_NAME" in normalized
            and "FROM INVOCATIONS I" in normalized
            and "JOIN AGENTS A" in normalized
            and "WHERE I.ID = $1" in normalized
        ):
            invocation_id, owner_id = args
            record = self.invocations.get(invocation_id)
            if not record:
                return None
            agent = self.agents.get(record["agent_id"])
            if not agent or agent.get("owner_id") != owner_id:
                return None
            metadata = record.get("metadata")
            if isinstance(metadata, dict):
                metadata_copy = dict(metadata)
            else:
                metadata_copy = metadata
            return FakeRecord(
                {
                    **record,
                    "agent_name": agent.get("name"),
                    "agent_metadata": agent.get("metadata"),
                    "metadata": metadata_copy,
                }
            )

        raise NotImplementedError(f"Unsupported fetchrow query: {query}")

    @asynccontextmanager
    async def transaction(self):
        yield FakeConnection(self)

    async def _execute(self, query: str, *args: Any) -> str:
        normalized = " ".join(query.strip().split()).upper()

        if normalized.startswith("INSERT INTO AGENTS"):
            if len(args) == 8:  # Model A insert
                (
                    agent_id,
                    name,
                    owner_id,
                    model_type,
                    status,
                    runtime,
                    created_at,
                    metadata_json,
                ) = args
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
                    "health_status": None,
                    "health_checked_at": None,
                }
            else:  # Model B insert
                (
                    agent_id,
                    name,
                    owner_id,
                    model_type,
                    status,
                    endpoint_url,
                    auth_config_json,
                    rate_limit_json,
                    created_at,
                    deployed_at,
                    health_status,
                    health_checked_at,
                    metadata_json,
                ) = args
                auth_config = json.loads(auth_config_json) if isinstance(auth_config_json, str) else auth_config_json
                rate_limit_config = json.loads(rate_limit_json) if isinstance(rate_limit_json, str) else rate_limit_json
                metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
                self.agents[agent_id] = {
                    "id": agent_id,
                    "name": name,
                    "owner_id": owner_id,
                    "model_type": model_type,
                    "status": status,
                    "runtime": None,
                    "image_ref": None,
                    "endpoint_url": endpoint_url,
                    "auth_config": auth_config or {},
                    "rate_limit_config": rate_limit_config or {},
                    "metadata": metadata or {},
                    "created_at": created_at,
                    "deployed_at": deployed_at,
                    "updated_at": created_at,
                    "health_status": health_status,
                    "health_checked_at": health_checked_at,
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

        if normalized.startswith("UPDATE AGENTS SET HEALTH_STATUS"):
            health_status, health_checked_at, agent_id = args
            agent = self.agents.get(agent_id)
            if agent:
                agent.update({
                    "health_status": health_status,
                    "health_checked_at": health_checked_at,
                    "updated_at": health_checked_at,
                })
                return "UPDATE 1"
            return "UPDATE 0"

        if normalized.startswith("UPDATE AGENTS SET METADATA = METADATA || $1"):
            metadata_patch_json, updated_at, agent_id = args
            patch = json.loads(metadata_patch_json)
            agent = self.agents.get(agent_id)
            if agent:
                current = agent.get("metadata") or {}
                current.update(patch)
                agent["metadata"] = current
                agent["updated_at"] = updated_at
                return "UPDATE 1"
            return "UPDATE 0"

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
                "id": invocation_id,
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
    concurrency_limit: Optional[int] = None,
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

    if concurrency_limit is not None:
        payload["concurrency_limit"] = concurrency_limit

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
