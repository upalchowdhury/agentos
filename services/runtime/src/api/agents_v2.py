"""
Enhanced Agents API - Supports Model A and Model B
Following newfeaturesAGENTREGISTRY.md specification
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.responses import JSONResponse

from ..agents.executor import AgentExecutor
from ..agents.builder import AgentBuilder  # NEW: Build images for Model A
from ..agents.proxy import ExternalAgentProxy  # NEW: Proxy for Model B
from ..database import db
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
        deployment_id = uuid.uuid4()
        
        # Insert agent record
        agent_query = """
        INSERT INTO agents (
            id, name, owner_id, model_type, status, runtime, created_at, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await db.execute(
            agent_query,
            agent_id,
            request.name,
            user_id,
            ModelType.A.value,
            AgentStatus.PENDING.value,
            request.runtime.value,
            datetime.utcnow(),
            json.dumps({
                "requirements": request.requirements,
                "resources": request.resources or {"cpu": "500m", "mem": "512Mi"}
            })
        )
        
        # Create agent version record
        version_query = """
        INSERT INTO agent_versions (
            id, agent_id, version_number, requirements_json, env_json, resources_json, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        await db.execute(
            version_query,
            deployment_id,
            agent_id,
            1,  # version 1
            json.dumps(request.requirements),
            json.dumps(request.env),  # TODO: Encrypt sensitive values
            json.dumps(request.resources or {"cpu": "500m", "mem": "512Mi"}),
            datetime.utcnow()
        )
        
        # Generate signed upload URL (stub - integrate with S3/minio)
        upload_url = f"https://artifacts.agentos.io/upload/{agent_id}/{deployment_id}?sig=stub"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        logger.info(f"Created Model A agent {agent_id} for user {user_id}")
        
        return UploadArtifactResponse(
            agent_id=str(agent_id),
            upload_url=upload_url,
            deployment_id=str(deployment_id),
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
        
        deployment_id = version['id']
        
        # Save artifact (stub - save to S3/minio)
        artifact_uri = f"s3://agentos-artifacts/{agent_id}/{deployment_id}.zip"
        
        # Update version with artifact info
        await db.execute("""
            UPDATE agent_versions
            SET artifact_uri = $1,
                artifact_checksum = $2,
                artifact_size_bytes = $3,
                build_status = $4
            WHERE id = $5
        """, artifact_uri, actual_checksum, len(contents), BuildStatus.IN_PROGRESS.value, deployment_id)
        
        # Update agent status
        await db.execute(
            "UPDATE agents SET status = $1 WHERE id = $2",
            AgentStatus.BUILDING.value,
            uuid.UUID(agent_id)
        )
        
        # Trigger build (async - using background job queue in production)
        # For now, return immediately with IN_PROGRESS status
        logger.info(f"Artifact uploaded for agent {agent_id}, triggering build")
        
        # TODO: Trigger actual build pipeline
        # await AgentBuilder.build_image(agent_id, deployment_id, artifact_uri)
        
        return BuildStatusResponse(
            agent_id=agent_id,
            deployment_id=str(deployment_id),
            status=BuildStatus.IN_PROGRESS,
            logs=["Artifact received", "Starting build pipeline..."],
            image_ref=None,
            error=None,
            started_at=datetime.utcnow(),
            completed_at=None
        )
        
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
        
        # Insert agent record
        query = """
        INSERT INTO agents (
            id, name, owner_id, model_type, status, 
            endpoint_url, auth_config, rate_limit_config,
            created_at, deployed_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        
        now = datetime.utcnow()
        
        await db.execute(
            query,
            agent_id,
            request.name,
            user_id,
            ModelType.B.value,
            AgentStatus.RUNNING.value,  # External agents are immediately "running"
            str(request.endpoint_url),
            json.dumps(request.auth.dict()),
            json.dumps(request.rate_limit.dict()),
            now,
            now
        )
        
        logger.info(f"Registered Model B agent {agent_id} pointing to {request.endpoint_url}")
        
        # TODO: Trigger health check
        # await ExternalAgentProxy.health_check(agent_id)
        
        return AgentResponse(
            agent_id=str(agent_id),
            name=request.name,
            owner_id=user_id,
            model_type=ModelType.B,
            status=AgentStatus.RUNNING,
            endpoint_url=str(request.endpoint_url),
            health_status="unknown",
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
        
        return AgentResponse(
            agent_id=str(agent['id']),
            name=agent['name'],
            owner_id=agent['owner_id'],
            model_type=ModelType(agent['model_type']),
            status=AgentStatus(agent['status']),
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
        agent = await db.fetchrow("""
            SELECT id, model_type, status, runtime, image_ref, endpoint_url, auth_config
            FROM agents
            WHERE id = $1
        """, uuid.UUID(agent_id))
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent['status'] != AgentStatus.RUNNING.value:
            raise HTTPException(status_code=503, detail=f"Agent status is {agent['status']}")
        
        # TODO: Check RBAC/OPA
        # decision = await opa_client.check_permission(user_id, agent_id, "invoke")
        # if not decision['allow']:
        #     return InvocationResult with status=DENIED
        
        invocation_id = uuid.uuid4()
        started_at = datetime.utcnow()
        
        # Route based on model type
        if agent['model_type'] == ModelType.A.value:
            # Model A: Execute code on our infrastructure
            result = await _execute_model_a(agent, request.input_data, request.timeout)
        else:
            # Model B: Proxy to external endpoint
            result = await _execute_model_b(agent, request.input_data, request.timeout)
        
        ended_at = datetime.utcnow()
        execution_time_ms = int((ended_at - started_at).total_seconds() * 1000)
        
        # Calculate cost (stub - integrate with cost calculator)
        cost = 0.01  # Stub value
        
        # Record invocation
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
            json.dumps(request.input_data),
            json.dumps(result.get('result')),
            result.get('status', InvocationStatus.SUCCESS.value),
            started_at,
            ended_at,
            execution_time_ms,
            cost,
            json.dumps(result.get('metadata', {}))
        )
        
        logger.info(f"Invoked agent {agent_id}, invocation_id {invocation_id}, status {result.get('status')}")
        
        return InvocationResult(
            invocation_id=str(invocation_id),
            agent_id=agent_id,
            status=InvocationStatus(result.get('status', InvocationStatus.SUCCESS.value)),
            result=result.get('result'),
            error=result.get('error'),
            execution_time_ms=execution_time_ms,
            cost=cost,
            metadata=result.get('metadata', {}),
            invoked_at=started_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invoke agent: {e}")
        raise HTTPException(status_code=500, detail=f"Invocation failed: {str(e)}")


async def _execute_model_a(agent, input_data: dict, timeout: int) -> dict:
    """Execute Model A agent (code on our infrastructure)"""
    # Get latest version code
    version = await db.fetchrow("""
        SELECT v.id, d.code
        FROM agent_versions v
        JOIN agent_deployments d ON v.agent_id = d.agent_did::uuid
        WHERE v.agent_id = $1 AND v.build_status = 'SUCCESS'
        ORDER BY v.version_number DESC
        LIMIT 1
    """, agent['id'])
    
    if not version:
        return {
            'status': InvocationStatus.ERROR.value,
            'error': 'No successful build found for agent',
            'result': None
        }
    
    # Execute using executor
    try:
        result = await executor.execute(
            agent_id=str(agent['id']),
            code=version['code'],
            input_data=input_data,
            timeout=timeout
        )
        return {
            'status': InvocationStatus.SUCCESS.value,
            'result': result,
            'error': None
        }
    except Exception as e:
        return {
            'status': InvocationStatus.ERROR.value,
            'result': None,
            'error': str(e)
        }


async def _execute_model_b(agent, input_data: dict, timeout: int) -> dict:
    """Execute Model B agent (proxy to external endpoint)"""
    # TODO: Implement external proxy
    # proxy = ExternalAgentProxy(agent['endpoint_url'], agent['auth_config'])
    # result = await proxy.invoke(input_data, timeout)
    
    # Stub implementation
    return {
        'status': InvocationStatus.SUCCESS.value,
        'result': {
            'message': 'Model B proxy not yet implemented',
            'input_received': input_data
        },
        'error': None,
        'metadata': {
            'endpoint': agent['endpoint_url'],
            'model_type': 'B'
        }
    }


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
