"""
Enhanced Agents API - Supports Model A and Model B
Following newfeaturesAGENTREGISTRY.md specification
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.responses import JSONResponse

from ..agents.builder import agent_builder
from ..agents.concurrency import concurrency_manager
from ..agents.executor import AgentExecutor
from ..agents.proxy import ExternalAgentProxy  # NEW: Proxy for Model B
from ..alerts import alert_manager
from ..agents.rate_limit import rate_limit_manager
from ..config import settings
from ..database import db
from ..opa_client import OPAClient
from ..models_v2 import (
    ModelType,
    AgentStatus,
    InvocationStatus,
    CreateModelARequest,
    CreateModelBRequest,
    UploadArtifactResponse,
    AgentResponse,
    InvocationRequest,
    InvocationResult,
    BuildStatusResponse,
    BuildStatus,
    AgentMetricsResponse,
    AgentCostResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/agents", tags=["agents"])
executor = AgentExecutor()
opa_client = OPAClient(settings.OPA_URL) if settings.OPA_URL else None


async def _apply_policy_obligations(
    obligations: Dict[str, Any],
    *,
    input_data: Optional[dict] = None,
    output_data: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> tuple[Optional[dict], Optional[Any], Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply policy obligations (e.g., PII redaction) to invocation artifacts.
    Returns sanitized copies of input/output/metadata plus enforcement summary.
    """
    if not obligations or opa_client is None:
        return input_data, output_data, metadata, {}

    enforcement = await opa_client.apply_obligations(
        obligations,
        input_data=input_data,
        output_data=output_data,
        metadata=metadata,
    )

    sanitized_input = enforcement.get("input_data", input_data)
    sanitized_output = enforcement.get("output_data", output_data)
    sanitized_metadata = enforcement.get("metadata", metadata)
    enforcement_summary = enforcement.get("applied", {})

    return sanitized_input, sanitized_output, sanitized_metadata, enforcement_summary


def _load_metadata(agent_row) -> dict:
    metadata = agent_row.get("metadata") if isinstance(agent_row, dict) else agent_row['metadata']
    if metadata is None:
        return {}
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    return metadata or {}


def _resolve_concurrency_limit(metadata: dict) -> int:
    limits = metadata.get("limits") or {}
    limit = limits.get("concurrency") or metadata.get("concurrency_limit")
    try:
        return int(limit) if limit is not None else settings.DEFAULT_CONCURRENCY_LIMIT
    except (ValueError, TypeError):  # pragma: no cover - defensive
        return settings.DEFAULT_CONCURRENCY_LIMIT


def _resolve_rate_limit(agent_row, metadata: dict) -> Tuple[float, int]:
    config = agent_row.get("rate_limit_config") if isinstance(agent_row, dict) else agent_row['rate_limit_config']
    if config is None:
        config = {}
    elif isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            config = {}

    rate_limits = metadata.get("rate_limit") or {}

    rps = rate_limits.get("rps", config.get("rps", 10.0))
    burst = rate_limits.get("burst", config.get("burst", 20))

    try:
        rps_val = max(0.1, float(rps))
    except (ValueError, TypeError):
        rps_val = 10.0

    try:
        burst_val = max(1, int(burst))
    except (ValueError, TypeError):
        burst_val = 20

    return rps_val, burst_val


def _build_partial_trace(
    agent_id: str,
    started_at: datetime,
    ended_at: datetime,
    status: str,
    endpoint: str,
) -> Dict[str, Any]:
    trace_id = uuid.uuid4().hex
    latency_ms = int((ended_at - started_at).total_seconds() * 1000)

    step = {
        "step_id": f"{trace_id}-step",
        "parent_step_id": None,
        "name": "external.invoke",
        "kind": "system",
        "start_ts": started_at,
        "end_ts": ended_at,
        "latency_ms": latency_ms,
        "status": status,
        "model_provider": None,
        "tokens_in": None,
        "tokens_out": None,
        "cost_cents": None,
        "error_type": None,
        "error_message": None,
        "input_excerpt": f"external call -> {endpoint}",
        "output_excerpt": None,
    }

    return {
        "trace_id": trace_id,
        "agent_id": agent_id,
        "status": status,
        "start_ts": started_at,
        "end_ts": ended_at,
        "execution_time_ms": latency_ms,
        "steps": [step],
    }


# ============================================================================
# AUTHENTICATION & AUTHORIZATION (stub - integrate with identity service)
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from JWT token
    In production: validate JWT, extract user/agent DID, check with identity service
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # TODO: Validate JWT with identity service
    # For now, return a stub user ID
    token = authorization.replace("Bearer ", "")
    return f"user_{token[:8]}"  # Stub: use first 8 chars as user ID


# ============================================================================
# MODEL A - CODE UPLOAD & DEPLOY
# ============================================================================

@router.post("/modelA", response_model=UploadArtifactResponse, status_code=201)
async def create_model_a_agent(
    request: CreateModelARequest,
    user_id: str = Depends(get_current_user)
):
    """
    Create Model A agent (code upload pattern)
    
    Flow:
    1. Create agent record (status: PENDING)
    2. Generate signed S3/minio upload URL
    3. Return upload URL
    4. Client uploads artifact to URL
    5. Trigger build pipeline (see upload_artifact endpoint)
    """
    try:
        agent_id = uuid.uuid4()
        version_id = uuid.uuid4()
        
        # Insert agent record
        agent_query = """
        INSERT INTO agents (
            id, name, owner_id, model_type, status, runtime, created_at, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        concurrency_limit = request.concurrency_limit or settings.DEFAULT_CONCURRENCY_LIMIT

        agent_metadata = {
            "requirements": request.requirements,
            "resources": request.resources or {"cpu": "500m", "mem": "512Mi"},
            "limits": {"concurrency": concurrency_limit},
            "telemetry_quality": "verified",
        }
        if request.alerts:
            agent_metadata["alerts"] = request.alerts.model_dump(exclude_none=True)

        await db.execute(
            agent_query,
            agent_id,
            request.name,
            user_id,
            ModelType.A.value,
            AgentStatus.PENDING.value,
            request.runtime.value,
            datetime.utcnow(),
            json.dumps(agent_metadata)
        )
        
        # Create agent version record
        version_query = """
        INSERT INTO agent_versions (
            id,
            agent_id,
            version_number,
            artifact_uri,
            requirements_json,
            env_json,
            resources_json,
            created_at,
            build_status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        await db.execute(
            version_query,
            version_id,
            agent_id,
            1,
            f"pending://{version_id}",
            json.dumps(request.requirements),
            json.dumps(request.env or {}),
            json.dumps(request.resources or {"cpu": "500m", "mem": "512Mi"}),
            datetime.utcnow(),
            BuildStatus.PENDING.value,
        )
        
        # Generate signed upload URL (stub - integrate with S3/minio)
        upload_url = f"https://artifacts.agentos.io/upload/{agent_id}/{version_id}?sig=stub"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        logger.info(f"Created Model A agent {agent_id} for user {user_id}")
        
        return UploadArtifactResponse(
            agent_id=str(agent_id),
            upload_url=upload_url,
            deployment_id=str(version_id),
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create Model A agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")


@router.put("/{agent_id}/artifact", response_model=BuildStatusResponse, status_code=202)
async def upload_artifact(
    agent_id: str,
    file: UploadFile = File(...),
    checksum: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user)
):
    """
    Upload code artifact (zip or single file) and trigger build
    
    Flow:
    1. Validate agent exists and user owns it
    2. Save artifact to storage
    3. Trigger build pipeline (Dockerfile + buildpack)
    4. Return build job status
    """
    try:
        # Verify agent ownership
        agent = await db.fetchrow(
            "SELECT id, owner_id, model_type FROM agents WHERE id = $1",
            uuid.UUID(agent_id)
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent['owner_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if agent['model_type'] != ModelType.A.value:
            raise HTTPException(status_code=400, detail="Only Model A agents support artifact upload")
        
        # Read and validate artifact
        contents = await file.read()
        actual_checksum = hashlib.sha256(contents).hexdigest()
        
        if checksum and checksum != actual_checksum:
            raise HTTPException(status_code=400, detail="Checksum mismatch")
        
        # Get latest version
        version = await db.fetchrow(
            "SELECT id FROM agent_versions WHERE agent_id = $1 ORDER BY version_number DESC LIMIT 1",
            uuid.UUID(agent_id)
        )
        
        if not version:
            raise HTTPException(status_code=404, detail="No version found for agent")
        
        version_id = version['id']
        
        await db.execute(
            "UPDATE agents SET status = $1 WHERE id = $2",
            AgentStatus.BUILDING.value,
            uuid.UUID(agent_id)
        )

        await db.execute(
            """
            UPDATE agent_versions
            SET build_status = $1,
                build_logs = $2
            WHERE id = $3
            """,
            BuildStatus.IN_PROGRESS.value,
            "Artifact received",
            version_id,
        )

        try:
            build_response = await agent_builder.build_image(
                uuid.UUID(agent_id),
                version_id,
                contents,
                file.filename or "agent.py",
            )
        except Exception as exc:
            await agent_builder.mark_failure(
                uuid.UUID(agent_id),
                version_id,
                str(exc),
                logs=["Build pipeline failed"],
            )
            logger.error("Build failed for agent %s: %s", agent_id, exc)
            raise HTTPException(status_code=500, detail=f"Build failed: {exc}") from exc
        
        logger.info("Artifact processed for agent %s", agent_id)
        return build_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload artifact: {e}")
        raise HTTPException(status_code=500, detail=f"Artifact upload failed: {str(e)}")


@router.get("/{agent_id}/build", response_model=BuildStatusResponse)
async def get_build_status(
    agent_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get build status for Model A agent"""
    try:
        version = await db.fetchrow("""
            SELECT 
                v.id, v.build_status, v.build_logs, v.build_error, 
                v.image_ref, v.created_at, v.built_at
            FROM agent_versions v
            JOIN agents a ON v.agent_id = a.id
            WHERE a.id = $1 AND a.owner_id = $2
            ORDER BY v.version_number DESC
            LIMIT 1
        """, uuid.UUID(agent_id), user_id)
        
        if not version:
            raise HTTPException(status_code=404, detail="Agent not found or not authorized")
        
        return BuildStatusResponse(
            agent_id=agent_id,
            deployment_id=str(version['id']),
            status=BuildStatus(version['build_status']),
            logs=version['build_logs'].split('\n') if version['build_logs'] else [],
            image_ref=version['image_ref'],
            error=version['build_error'],
            started_at=version['created_at'],
            completed_at=version['built_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get build status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL B - REGISTRY (External Agents)
# ============================================================================

@router.post("/modelB", response_model=AgentResponse, status_code=201)
async def create_model_b_agent(
    request: CreateModelBRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Register external agent endpoint (Model B)
    
    Examples:
    - OpenAI Assistants API
    - Salesforce Agentforce
    - MCP agents on customer infrastructure
    - Any HTTPS endpoint following the contract
    """
    try:
        agent_id = uuid.uuid4()

        health_path = request.health_check_path or "/health"
        proxy = ExternalAgentProxy(
            endpoint_url=str(request.endpoint_url),
            auth_config=request.auth.model_dump(),
            timeout=request.timeout_seconds,
            rate_limit=request.rate_limit.model_dump(),
        )

        is_healthy = await proxy.health_check(health_path)
        health_status = "healthy" if is_healthy else "unhealthy"

        metadata = {
            "health_check_path": health_path,
            "rate_limit": request.rate_limit.model_dump(),
            "timeout_seconds": request.timeout_seconds,
            "telemetry_quality": "partial",
        }
        if request.alerts:
            metadata["alerts"] = request.alerts.model_dump(exclude_none=True)

        now = datetime.utcnow()

        query = """
        INSERT INTO agents (
            id, name, owner_id, model_type, status,
            endpoint_url, auth_config, rate_limit_config,
            created_at, deployed_at,
            health_status, health_checked_at, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """

        await db.execute(
            query,
            agent_id,
            request.name,
            user_id,
            ModelType.B.value,
            AgentStatus.RUNNING.value,
            str(request.endpoint_url),
            json.dumps(request.auth.model_dump()),
            json.dumps(request.rate_limit.model_dump()),
            now,
            now,
            health_status,
            now,
            json.dumps(metadata),
        )

        logger.info(f"Registered Model B agent {agent_id} pointing to {request.endpoint_url}")

        return AgentResponse(
            agent_id=str(agent_id),
            name=request.name,
            owner_id=user_id,
            model_type=ModelType.B,
            status=AgentStatus.RUNNING,
            endpoint_url=str(request.endpoint_url),
            health_status=health_status,
            telemetry_quality="partial",
            created_at=now,
            deployed_at=now,
            invocation_count=0,
            cost_to_date=0.0
        )
        
    except Exception as e:
        logger.error(f"Failed to register Model B agent: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


# ============================================================================
# UNIFIED AGENT OPERATIONS
# ============================================================================

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get agent details (works for Model A and B)"""
    try:
        agent = await db.fetchrow("""
            SELECT 
                a.*,
                COUNT(i.id) as invocation_count,
                COALESCE(SUM(i.cost_decimal), 0) as cost_to_date
            FROM agents a
            LEFT JOIN invocations i ON a.id = i.agent_id
            WHERE a.id = $1 AND a.owner_id = $2
            GROUP BY a.id
        """, uuid.UUID(agent_id), user_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found or not authorized")
        
        metadata = _load_metadata(agent)
        telemetry_quality = metadata.get("telemetry_quality")
        if not telemetry_quality:
            telemetry_quality = "verified" if agent['model_type'] == ModelType.A.value else "partial"

        return AgentResponse(
            agent_id=str(agent['id']),
            name=agent['name'],
            owner_id=agent['owner_id'],
            model_type=ModelType(agent['model_type']),
            status=AgentStatus(agent['status']),
            telemetry_quality=telemetry_quality,
            runtime=agent['runtime'],
            image_ref=agent['image_ref'],
            endpoint_url=agent['endpoint_url'],
            health_status=agent['health_status'],
            created_at=agent['created_at'],
            deployed_at=agent['deployed_at'],
            invocation_count=agent['invocation_count'],
            cost_to_date=float(agent['cost_to_date'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete agent (sets status to TERMINATED)"""
    try:
        result = await db.execute("""
            UPDATE agents
            SET status = $1, updated_at = $2
            WHERE id = $3 AND owner_id = $4
        """, AgentStatus.TERMINATED.value, datetime.utcnow(), uuid.UUID(agent_id), user_id)
        
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Agent not found or not authorized")
        
        logger.info(f"Deleted agent {agent_id}")
        return JSONResponse(status_code=204, content={})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INVOCATION (Unified for Model A & B)
# ============================================================================

@router.post("/{agent_id}/invoke", response_model=InvocationResult)
async def invoke_agent(
    agent_id: str,
    request: InvocationRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Invoke agent (works for both Model A and Model B)
    
    Flow:
    1. Check agent exists and is RUNNING
    2. Check RBAC/OPA permissions (TODO: integrate with OPA)
    3. Route to executor (Model A) or proxy (Model B)
    4. Record invocation in database
    5. Return standardized result envelope
    """
    try:
        # Get agent details
        agent = await db.fetchrow(
            """
            SELECT
                id,
                owner_id,
                model_type,
                status,
                runtime,
                image_ref,
                endpoint_url,
                auth_config,
                rate_limit_config,
                metadata
            FROM agents
            WHERE id = $1
            """,
            uuid.UUID(agent_id),
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent['status'] != AgentStatus.RUNNING.value:
            raise HTTPException(status_code=503, detail=f"Agent status is {agent['status']}")

        agent_metadata = _load_metadata(agent)

        invocation_id = uuid.uuid4()
        started_at = datetime.utcnow()

        policy_obligations: dict = {}

        if opa_client:
            decision = await opa_client.check_invoke_permission(
                subject_id=user_id,
                subject_type="user",
                agent_id=agent_id,
                agent_data={
                    "owner_id": agent.get("owner_id"),
                    "model_type": agent['model_type'],
                    "metadata": agent_metadata,
                },
                caller_agent_id=request.caller_agent_id,
            )

            if not decision.get("allow", False):
                ended_at = datetime.utcnow()
                execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)

                await db.execute(
                    """
                    INSERT INTO invocations (
                        id, agent_id, requester_id, caller_agent_id,
                        input_data, output_data, status,
                        started_at, ended_at, execution_time_ms,
                        cost_decimal, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    invocation_id,
                    uuid.UUID(agent_id),
                    user_id,
                    uuid.UUID(request.caller_agent_id) if request.caller_agent_id else None,
                    json.dumps(request.input_data, default=str),
                    json.dumps(None),
                    InvocationStatus.DENIED.value,
                    started_at,
                    ended_at,
                execution_time_ms,
                0.0,
                json.dumps({"opa": decision, "actor": {"requester_id": user_id, "caller_agent_id": request.caller_agent_id}}, default=str),
            )

                logger.info(
                    "Invocation denied by OPA for agent %s (decision: %s)",
                    agent_id,
                    decision.get("deny_reason"),
                )

                return InvocationResult(
                    invocation_id=str(invocation_id),
                    agent_id=agent_id,
                    status=InvocationStatus.DENIED,
                    result=None,
                error=decision.get("deny_reason", "not_authorized"),
                execution_time_ms=execution_time_ms,
                cost=0.0,
                metadata={
                    "opa": decision,
                    "actor": {
                        "requester_id": user_id,
                        "caller_agent_id": str(request.caller_agent_id) if request.caller_agent_id else None,
                        "subject_type": "agent" if request.caller_agent_id else "user",
                        "subject_id": str(request.caller_agent_id) if request.caller_agent_id else user_id,
                    },
                },
                invoked_at=started_at,
            )
            policy_obligations = decision.get("obligations", {})

        caller_context: Dict[str, Any] = {
            "requester_id": user_id,
            "caller_agent_id": str(request.caller_agent_id) if request.caller_agent_id else None,
            "subject_type": "agent" if request.caller_agent_id else "user",
            "subject_id": str(request.caller_agent_id) if request.caller_agent_id else user_id,
        }

        concurrency_limit = _resolve_concurrency_limit(agent_metadata)
        acquired_concurrency = await concurrency_manager.try_acquire(str(agent["id"]), concurrency_limit)
        if not acquired_concurrency:
            ended_at = datetime.utcnow()
            execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)
            error_message = f"Concurrency limit reached ({concurrency_limit})"

            base_metadata: Dict[str, Any] = {
                "limits": {"concurrency": concurrency_limit},
                "logs": [
                    {
                        "timestamp": ended_at.isoformat(),
                        "level": "WARNING",
                        "message": error_message,
                        "trace_id": None,
                    }
                ],
                "actor": caller_context,
            }
            if policy_obligations:
                base_metadata["policy"] = {"obligations": policy_obligations}

            sanitized_input, _, sanitized_metadata, enforcement_summary = await _apply_policy_obligations(
                policy_obligations,
                input_data=request.input_data,
                metadata=base_metadata,
            )
            stored_input = sanitized_input if sanitized_input is not None else request.input_data
            sanitized_metadata = sanitized_metadata or base_metadata
            sanitized_metadata.setdefault("actor", caller_context)
            if policy_obligations:
                policy_section = sanitized_metadata.setdefault("policy", {})
                policy_section.setdefault("obligations", policy_obligations)
                if enforcement_summary:
                    policy_section["enforcement"] = enforcement_summary
            elif enforcement_summary:
                sanitized_metadata.setdefault("policy", {})["enforcement"] = enforcement_summary

            await db.execute(
                """
                INSERT INTO invocations (
                    id, agent_id, requester_id, caller_agent_id,
                    input_data, output_data, status,
                    started_at, ended_at, execution_time_ms,
                    cost_decimal, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                invocation_id,
                uuid.UUID(agent_id),
                user_id,
                uuid.UUID(request.caller_agent_id) if request.caller_agent_id else None,
                json.dumps(stored_input, default=str),
                json.dumps(None),
                InvocationStatus.ERROR.value,
                started_at,
                ended_at,
                execution_time_ms,
                0.0,
                json.dumps(sanitized_metadata, default=str),
            )

            await _update_cost_snapshot(
                agent_id=uuid.UUID(agent_id),
                owner_id=agent["owner_id"],
                occurred_at=started_at,
                status=InvocationStatus.ERROR.value,
                cost=0.0,
            )

            logger.warning("Concurrency limit reached for agent %s", agent_id)

            return InvocationResult(
                invocation_id=str(invocation_id),
                agent_id=agent_id,
                status=InvocationStatus.ERROR,
                result=None,
                error=error_message,
                execution_time_ms=execution_time_ms,
                cost=0.0,
                metadata=sanitized_metadata,
                invoked_at=started_at,
            )

        rate_limit_rps, rate_limit_burst = _resolve_rate_limit(agent, agent_metadata)
        policy_rate_limit = (
            policy_obligations.get("rate_limit")
            if isinstance(policy_obligations, dict)
            else None
        )
        if isinstance(policy_rate_limit, dict):
            policy_rps = policy_rate_limit.get("rps")
            policy_burst = policy_rate_limit.get("burst")
            try:
                if policy_rps is not None:
                    rate_limit_rps = max(0.1, float(policy_rps))
            except (TypeError, ValueError):  # pragma: no cover - fall back to configured values
                pass
            try:
                if policy_burst is not None:
                    rate_limit_burst = max(1, int(policy_burst))
            except (TypeError, ValueError):  # pragma: no cover - fall back to configured values
                pass
        if agent['model_type'] == ModelType.B.value:
            if not await rate_limit_manager.try_acquire(str(agent["id"]), rate_limit_rps, rate_limit_burst):
                ended_at = datetime.utcnow()
                execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)
                error_message = f"Rate limit exceeded ({rate_limit_rps} rps, burst {rate_limit_burst})"

                base_metadata: Dict[str, Any] = {
                    "rate_limit": {"rps": rate_limit_rps, "burst": rate_limit_burst},
                    "logs": [
                        {
                            "timestamp": ended_at.isoformat(),
                            "level": "WARNING",
                            "message": f"Rate limit exceeded ({rate_limit_rps} rps, burst {rate_limit_burst})",
                            "trace_id": None,
                        }
                    ],
                    "actor": caller_context,
                }
                if policy_obligations:
                    base_metadata["policy"] = {"obligations": policy_obligations}

                sanitized_input, _, sanitized_metadata, enforcement_summary = await _apply_policy_obligations(
                    policy_obligations,
                    input_data=request.input_data,
                    metadata=base_metadata,
                )
                stored_input = sanitized_input if sanitized_input is not None else request.input_data
                sanitized_metadata = sanitized_metadata or base_metadata
                sanitized_metadata.setdefault("actor", caller_context)
                if policy_obligations:
                    policy_section = sanitized_metadata.setdefault("policy", {})
                    policy_section.setdefault("obligations", policy_obligations)
                    if enforcement_summary:
                        policy_section["enforcement"] = enforcement_summary
                elif enforcement_summary:
                    sanitized_metadata.setdefault("policy", {})["enforcement"] = enforcement_summary

                await db.execute(
                    """
                    INSERT INTO invocations (
                        id, agent_id, requester_id, caller_agent_id,
                        input_data, output_data, status,
                        started_at, ended_at, execution_time_ms,
                        cost_decimal, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    invocation_id,
                    uuid.UUID(agent_id),
                    user_id,
                    uuid.UUID(request.caller_agent_id) if request.caller_agent_id else None,
                    json.dumps(stored_input, default=str),
                    json.dumps(None),
                    InvocationStatus.ERROR.value,
                    started_at,
                    ended_at,
                    execution_time_ms,
                    0.0,
                    json.dumps(sanitized_metadata, default=str),
                )

                await _update_cost_snapshot(
                    agent_id=uuid.UUID(agent_id),
                    owner_id=agent["owner_id"],
                    occurred_at=started_at,
                    status=InvocationStatus.ERROR.value,
                    cost=0.0,
                )

                logger.warning("Rate limit exceeded for agent %s", agent_id)

                raise HTTPException(status_code=429, detail="Rate limit exceeded")

        try:
            # Route based on model type
            if agent['model_type'] == ModelType.A.value:
                # Model A: Execute code on our infrastructure
                result = await _execute_model_a(agent, request.input_data, request.timeout)
            else:
                # Model B: Proxy to external endpoint
                result = await _execute_model_b(agent, request.input_data, request.timeout)
        finally:
            await concurrency_manager.release(str(agent["id"]))

        ended_at = datetime.utcnow()
        execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)

        cost = float(result.get('cost', 0.0) or 0.0)

        # Record invocation
        result_metadata = result.get('metadata', {}) or {}
        if not isinstance(result_metadata, dict):  # pragma: no cover - defensive
            result_metadata = {}
        result_metadata.setdefault("limits", {})["concurrency"] = concurrency_limit
        if agent['model_type'] == ModelType.B.value:
            result_metadata.setdefault("limits", {})["rate_limit"] = {
                "rps": rate_limit_rps,
                "burst": rate_limit_burst,
            }
            if result_metadata.get("telemetry_quality") == "verified" and agent_metadata.get("telemetry_quality") != "verified":
                await _update_agent_metadata(agent["id"], {"telemetry_quality": "verified"})
        if policy_obligations:
            result_metadata = {**result_metadata, "opa_obligations": policy_obligations}
        result_metadata.setdefault("actor", caller_context)

        trace = result_metadata.get("trace")
        if isinstance(trace, dict):
            trace.setdefault("trace_id", uuid.uuid4().hex)
            trace["invocation_id"] = str(invocation_id)
            trace.setdefault("agent_id", str(agent["id"]))
            trace.setdefault("start_ts", started_at)
            trace.setdefault("end_ts", ended_at)
            trace.setdefault(
                "execution_time_ms",
                int((trace.get("end_ts") - trace.get("start_ts")).total_seconds() * 1000)
                if isinstance(trace.get("start_ts"), datetime) and isinstance(trace.get("end_ts"), datetime)
                else execution_time_ms,
            )
            steps = trace.setdefault("steps", [])
            for idx, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue
                step.setdefault("step_id", f"{trace['trace_id']}-step-{idx}")
                step.setdefault("status", result.get('status', InvocationStatus.SUCCESS.value))

        log_entry = {
            "timestamp": ended_at.isoformat(),
            "level": "INFO",
            "message": f"Invocation {invocation_id} completed with status {result.get('status')}",
            "trace_id": trace.get("trace_id") if isinstance(trace, dict) else None,
            "actor": caller_context,
        }
        logs = result_metadata.get("logs")
        if isinstance(logs, list):
            logs.append(log_entry)
        else:
            result_metadata["logs"] = [log_entry]

        stored_input, stored_output, sanitized_metadata, enforcement_summary = await _apply_policy_obligations(
            policy_obligations,
            input_data=request.input_data,
            output_data=result.get('result'),
            metadata=result_metadata,
        )
        stored_input = stored_input if stored_input is not None else request.input_data
        stored_output = stored_output if stored_output is not None else result.get('result')
        sanitized_metadata = sanitized_metadata or result_metadata
        sanitized_metadata.setdefault("actor", caller_context)

        policy_section: Optional[Dict[str, Any]] = sanitized_metadata.get("policy")
        if policy_obligations:
            policy_section = sanitized_metadata.setdefault("policy", {})
            policy_section.setdefault("obligations", policy_obligations)
            if enforcement_summary:
                policy_section["enforcement"] = enforcement_summary
        elif enforcement_summary:
            policy_section = sanitized_metadata.setdefault("policy", {})
            policy_section["enforcement"] = enforcement_summary

        if isinstance(policy_rate_limit, dict):
            policy_section = sanitized_metadata.setdefault("policy", {}) if policy_section is None else policy_section
            policy_section["effective_rate_limit"] = {
                "rps": rate_limit_rps,
                "burst": rate_limit_burst,
            }

        await db.execute("""
            INSERT INTO invocations (
                id, agent_id, requester_id, caller_agent_id,
                input_data, output_data, status,
                started_at, ended_at, execution_time_ms,
                cost_decimal, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
            invocation_id,
            uuid.UUID(agent_id),
            user_id,
            uuid.UUID(request.caller_agent_id) if request.caller_agent_id else None,
            json.dumps(stored_input, default=str),
            json.dumps(stored_output, default=str),
            result.get('status', InvocationStatus.SUCCESS.value),
            started_at,
            ended_at,
            execution_time_ms,
            cost,
            json.dumps(sanitized_metadata, default=str)
        )

        await _update_cost_snapshot(
            agent_id=uuid.UUID(agent_id),
            owner_id=agent["owner_id"],
            occurred_at=started_at,
            status=result.get('status', InvocationStatus.SUCCESS.value),
            cost=cost,
        )

        await alert_manager.evaluate(
            agent_id=str(agent["id"]),
            agent_name=agent.get("name", agent_id),
            telemetry_quality=result_metadata.get("telemetry_quality") or agent_metadata.get("telemetry_quality"),
        )

        logger.info(f"Invoked agent {agent_id}, invocation_id {invocation_id}, status {result.get('status')}")

        return InvocationResult(
            invocation_id=str(invocation_id),
            agent_id=agent_id,
            status=InvocationStatus(result.get('status', InvocationStatus.SUCCESS.value)),
            result=stored_output,
            error=result.get('error'),
            execution_time_ms=execution_time_ms,
            cost=cost,
            metadata=sanitized_metadata,
            invoked_at=started_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invoke agent: {e}")
        raise HTTPException(status_code=500, detail=f"Invocation failed: {str(e)}")


async def _execute_model_a(agent, input_data: dict, timeout: int) -> dict:
    """Execute Model A agent (code on our infrastructure)"""
    deployment = await db.fetchrow(
        """
        SELECT id, code
        FROM agent_deployments
        WHERE agent_did = $1 AND status = $2
        ORDER BY deployed_at DESC
        LIMIT 1
        """,
        str(agent["id"]),
        AgentStatus.RUNNING.value,
    )

    if not deployment:
        return {
            "status": InvocationStatus.ERROR.value,
            "error": "No active deployment found for agent",
            "result": None,
        }

    try:
        execution_payload = await executor.execute(
            agent_id=str(agent["id"]),
            code=deployment["code"],
            input_data=input_data,
            timeout=timeout,
        )
        status = execution_payload.get("status", InvocationStatus.SUCCESS.value)
        metadata = {
            "deployment_id": str(deployment["id"]),
            "trace": execution_payload.get("trace"),
            "raw_execution": execution_payload,
        }
        return {
            "status": status,
            "result": execution_payload.get("output"),
            "metadata": metadata,
            "cost": execution_payload.get("cost_cents", 0) / 100,
            "error": execution_payload.get("error"),
        }
    except Exception as exc:  # pragma: no cover - surfaced in response
        return {
            "status": InvocationStatus.ERROR.value,
            "result": None,
            "error": str(exc),
            "metadata": {"deployment_id": str(deployment["id"])},
        }


async def _execute_model_b(agent, input_data: dict, timeout: int) -> dict:
    """Execute Model B agent (proxy to external endpoint)"""
    auth_config = agent["auth_config"] or {}
    rate_limit = agent["rate_limit_config"] or {}

    proxy = ExternalAgentProxy(
        agent["endpoint_url"],
        auth_config,
        timeout=timeout,
        rate_limit=rate_limit,
    )

    started_at = datetime.utcnow()
    try:
        proxy_result = await proxy.invoke(input_data, timeout)
        ended_at = datetime.utcnow()
    except Exception as exc:
        return {
            "status": InvocationStatus.ERROR.value,
            "result": None,
            "error": str(exc),
            "metadata": {"endpoint": agent["endpoint_url"]},
        }

    trace = proxy_result.get("metadata", {}).get("trace")
    telemetry_quality = proxy_result.get("metadata", {}).get("telemetry_quality", "partial")

    if not isinstance(trace, dict):
        trace = _build_partial_trace(
            agent_id=str(agent["id"]),
            started_at=started_at,
            ended_at=datetime.utcnow(),
            status=proxy_result.get("status", InvocationStatus.SUCCESS.value),
            endpoint=agent["endpoint_url"],
        )
        telemetry_quality = "partial"

    metadata = proxy_result.get("metadata", {}) or {}
    metadata.update(
        {
            "trace": trace,
            "telemetry_quality": telemetry_quality,
        }
    )

    return {
        "status": InvocationStatus.SUCCESS.value,
        "result": proxy_result.get("result"),
        "error": None,
        "metadata": metadata,
        "cost": proxy_result.get("cost", 0.0),
    }


def _period_bounds(timestamp: datetime) -> tuple[datetime, datetime]:
    """Calculate monthly cost snapshot window for a given timestamp."""
    period_start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1)
    return period_start, period_end


async def _update_cost_snapshot(
    agent_id: uuid.UUID,
    owner_id: str,
    occurred_at: datetime,
    status: str,
    cost: float,
) -> None:
    """Update cost snapshot aggregates for the agent."""
    try:
        period_start, period_end = _period_bounds(occurred_at)

        snapshot = await db.fetchrow(
            """
            SELECT total_invocations, successful_invocations, failed_invocations,
                   total_cost, compute_cost, llm_api_cost, storage_cost
            FROM cost_snapshots
            WHERE agent_id = $1 AND period_start = $2 AND period_end = $3
            """,
            agent_id,
            period_start,
            period_end,
        )

        success = 1 if status == InvocationStatus.SUCCESS.value else 0
        failure = 1 if status in {InvocationStatus.ERROR.value, InvocationStatus.TIMEOUT.value, InvocationStatus.DENIED.value} else 0

        if snapshot:
            await db.execute(
                """
                UPDATE cost_snapshots
                SET total_invocations = $1,
                    successful_invocations = $2,
                    failed_invocations = $3,
                    total_cost = $4,
                    compute_cost = $5,
                    llm_api_cost = $6,
                    storage_cost = $7
                WHERE agent_id = $8 AND period_start = $9 AND period_end = $10
                """,
                snapshot["total_invocations"] + 1,
                snapshot["successful_invocations"] + success,
                snapshot["failed_invocations"] + failure,
                float(snapshot["total_cost"]) + cost,
                float(snapshot["compute_cost"] or 0) + cost,
                float(snapshot["llm_api_cost"] or 0),
                float(snapshot["storage_cost"] or 0),
                agent_id,
                period_start,
                period_end,
            )
        else:
            snapshot_id = uuid.uuid4()
            await db.execute(
                """
                INSERT INTO cost_snapshots (
                    id, agent_id, owner_id,
                    period_start, period_end,
                    total_invocations, successful_invocations, failed_invocations,
                    total_cost, compute_cost, llm_api_cost, storage_cost,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                snapshot_id,
                agent_id,
                owner_id,
                period_start,
                period_end,
                1,
                success,
                failure,
                cost,
                cost,
                0.0,
                0.0,
                datetime.utcnow(),
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to update cost snapshot for agent %s: %s", agent_id, exc)


async def _update_agent_metadata(agent_id: uuid.UUID, patch: dict) -> None:
    try:
        await db.execute(
            """
            UPDATE agents
            SET metadata = metadata || $1,
                updated_at = $2
            WHERE id = $3
            """,
            json.dumps(patch),
            datetime.utcnow(),
            agent_id,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to update agent metadata for %s: %s", agent_id, exc)


# ============================================================================
# OBSERVABILITY
# ============================================================================

@router.get("/{agent_id}/metrics", response_model=AgentMetricsResponse)
async def get_agent_metrics(
    agent_id: str,
    range: str = "1d",
    user_id: str = Depends(get_current_user)
):
    """Get agent performance metrics"""
    # Parse range to time window
    range_map = {"1h": 1, "1d": 24, "7d": 168, "30d": 720}
    hours = range_map.get(range, 24)
    
    period_start = datetime.utcnow() - timedelta(hours=hours)
    period_end = datetime.utcnow()
    
    try:
        metrics = await db.fetchrow("""
            SELECT * FROM agent_stats_v2 WHERE agent_id = $1
        """, uuid.UUID(agent_id))
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentMetricsResponse(
            agent_id=agent_id,
            period_start=period_start,
            period_end=period_end,
            total_invocations=metrics['total_invocations'] or 0,
            successful_invocations=metrics['successful_invocations'] or 0,
            failed_invocations=metrics['failed_invocations'] or 0,
            denied_invocations=metrics['denied_invocations'] or 0,
            avg_execution_time_ms=float(metrics['avg_execution_time_ms'] or 0),
            p50_latency_ms=float(metrics['p50_latency_ms'] or 0),
            p95_latency_ms=float(metrics['p95_latency_ms'] or 0),
            p99_latency_ms=float(metrics['p99_latency_ms'] or 0),
            total_cost_usd=float(metrics['total_cost_usd'] or 0),
            error_rate=float(metrics['failed_invocations'] or 0) / max(metrics['total_invocations'] or 1, 1)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/costs", response_model=AgentCostResponse)
async def get_agent_costs(
    agent_id: str,
    period: str = "monthly",
    user_id: str = Depends(get_current_user)
):
    """Get agent cost breakdown"""
    try:
        # Get cost snapshot
        snapshot = await db.fetchrow("""
            SELECT *
            FROM cost_snapshots
            WHERE agent_id = $1
            ORDER BY period_end DESC
            LIMIT 1
        """, uuid.UUID(agent_id))
        
        if not snapshot:
            # No snapshot yet, return zeros
            return AgentCostResponse(
                agent_id=agent_id,
                period=period,
                total_cost_usd=0.0,
                invocations=0,
                cost_per_invocation_usd=0.0,
                breakdown={"compute": 0.0, "llm_api": 0.0, "storage": 0.0}
            )
        
        total = float(snapshot['total_cost'])
        invocations = snapshot['total_invocations']
        
        return AgentCostResponse(
            agent_id=agent_id,
            period=period,
            total_cost_usd=total,
            invocations=invocations,
            cost_per_invocation_usd=total / max(invocations, 1),
            breakdown={
                "compute": float(snapshot['compute_cost'] or 0),
                "llm_api": float(snapshot['llm_api_cost'] or 0),
                "storage": float(snapshot['storage_cost'] or 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
