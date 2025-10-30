import hashlib
import json
import logging
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..database import db
from ..models import AgentStatus
from ..models_v2 import BuildStatus, BuildStatusResponse
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class ArtifactDetails:
    path: Path
    size_bytes: int
    checksum: str
    code: str


class AgentBuilder:
    """
    Minimal build pipeline for Model A agents.

    The builder persists uploaded artifacts, extracts agent code, and wires up
    metadata in the database so that the executor can run the agent immediately.
    This is a synchronous implementation; in production it should be moved to a
    background worker or job queue.
    """

    def __init__(self) -> None:
        # Create artifacts directory within the configured path; fall back to CWD if unavailable
        configured_path = Path(settings.ARTIFACTS_DIR)
        try:
            configured_path.mkdir(parents=True, exist_ok=True)
            self._artifacts_dir = configured_path
        except OSError as exc:  # pragma: no cover - environment dependent
            fallback = Path.cwd() / "artifacts"
            fallback.mkdir(parents=True, exist_ok=True)
            logger.warning(
                "Failed to create artifacts directory %s (%s); falling back to %s",
                configured_path,
                exc,
                fallback,
            )
            self._artifacts_dir = fallback

    async def build_image(
        self,
        agent_id: uuid.UUID,
        version_id: uuid.UUID,
        artifact_bytes: bytes,
        filename: str,
    ) -> BuildStatusResponse:
        logger.info("Starting build for agent %s version %s", agent_id, version_id)
        started_at = datetime.utcnow()

        details = self._persist_artifact(agent_id, version_id, artifact_bytes, filename)
        logs: list[str] = [
            "Artifact persisted",
            f"Checksum: {details.checksum}",
            f"Size: {details.size_bytes} bytes",
        ]

        try:
            async with db.transaction() as conn:
                await conn.execute(
                    """
                    UPDATE agent_versions
                    SET artifact_uri = $1,
                        artifact_checksum = $2,
                        artifact_size_bytes = $3,
                        build_status = $4,
                        build_logs = $5,
                        image_ref = $6,
                        built_at = $7
                    WHERE id = $8
                    """,
                    str(details.path),
                    details.checksum,
                    details.size_bytes,
                    BuildStatus.SUCCESS.value,
                    "\n".join(logs + ["Build completed"]),
                    self._image_ref(agent_id, version_id),
                    datetime.utcnow(),
                    version_id,
                )

                await self._upsert_deployment(conn, agent_id, version_id, details.code)

                await conn.execute(
                    """
                    UPDATE agents
                    SET status = $1,
                        image_ref = $2,
                        deployed_at = $3,
                        updated_at = $3
                    WHERE id = $4
                    """,
                    AgentStatus.RUNNING.value,
                    self._image_ref(agent_id, version_id),
                    datetime.utcnow(),
                    agent_id,
                )
        except Exception as exc:  # pragma: no cover - surfaced to caller
            logger.exception("Build failed for agent %s: %s", agent_id, exc)
            raise

        completed_at = datetime.utcnow()
        logger.info("Build succeeded for agent %s", agent_id)
        return BuildStatusResponse(
            agent_id=str(agent_id),
            deployment_id=str(version_id),
            status=BuildStatus.SUCCESS,
            logs=logs + ["Build completed"],
            image_ref=self._image_ref(agent_id, version_id),
            error=None,
            started_at=started_at,
            completed_at=completed_at,
        )

    async def mark_failure(
        self,
        agent_id: uuid.UUID,
        version_id: uuid.UUID,
        error_message: str,
        logs: Optional[list[str]] = None,
    ) -> None:
        logs = logs or []
        async with db.transaction() as conn:
            await conn.execute(
                """
                UPDATE agent_versions
                SET build_status = $1,
                    build_error = $2,
                    build_logs = $3,
                    built_at = $4
                WHERE id = $5
                """,
                BuildStatus.FAILED.value,
                error_message,
                "\n".join(logs + [error_message]),
                datetime.utcnow(),
                version_id,
            )
            await conn.execute(
                """
                UPDATE agents
                SET status = $1,
                    updated_at = $2
                WHERE id = $3
                """,
                AgentStatus.FAILED.value,
                datetime.utcnow(),
                agent_id,
            )

    def _persist_artifact(
        self,
        agent_id: uuid.UUID,
        version_id: uuid.UUID,
        artifact_bytes: bytes,
        filename: str,
    ) -> ArtifactDetails:
        agent_dir = self._artifacts_dir / str(agent_id)
        agent_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(filename).suffix or ".bin"
        target_path = agent_dir / f"{version_id}{extension}"
        target_path.write_bytes(artifact_bytes)

        checksum = hashlib.sha256(artifact_bytes).hexdigest()
        code = self._extract_code(target_path, artifact_bytes)

        return ArtifactDetails(
            path=target_path,
            size_bytes=len(artifact_bytes),
            checksum=checksum,
            code=code,
        )

    def _extract_code(self, path: Path, artifact_bytes: bytes) -> str:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for candidate in ("main.py", "agent.py", "app.py"):
                    try:
                        with archive.open(candidate) as file_obj:
                            return file_obj.read().decode("utf-8")
                    except KeyError:
                        continue
                raise ValueError(
                    "Uploaded archive must contain main.py, agent.py, or app.py"
                )
        try:
            return artifact_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Artifact must be UTF-8 encoded Python source") from exc

    async def _upsert_deployment(
        self,
        conn,
        agent_id: uuid.UUID,
        version_id: uuid.UUID,
        code: str,
    ) -> None:
        resource = await conn.fetchrow(
            """
            SELECT resources_json, requirements_json, env_json
            FROM agent_versions
            WHERE id = $1
            """,
            version_id,
        )
        requirements = resource["requirements_json"] if resource else []
        environment = resource["env_json"] if resource else {}
        limits = resource["resources_json"] if resource else {}

        metadata = json.dumps(
            {
                "requirements": requirements,
                "environment": environment,
                "version_id": str(version_id),
            }
        )

        limits_json = json.dumps(limits)

        deployment_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO agent_deployments
            (id, agent_did, status, code, code_hash, resource_limits, deployed_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            deployment_id,
            str(agent_id),
            AgentStatus.RUNNING.value,
            code,
            self._code_hash(code),
            limits_json,
            datetime.utcnow(),
            metadata,
        )

    def _image_ref(self, agent_id: uuid.UUID, version_id: uuid.UUID) -> str:
        return f"agentos/runtime:{agent_id}-{version_id}"

    @staticmethod
    def _code_hash(code: str) -> int:
        return int(hashlib.sha256(code.encode("utf-8")).hexdigest()[:16], 16)


# Shared instance so uploads trigger the same builder.
agent_builder = AgentBuilder()
