import hashlib
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..agents.executor import AgentExecutor
from ..database import db
from ..models import (
    AgentStatus,
    AgentStatusResponse,
    DeploymentRequest,
    DeploymentResponse,
    InvocationRequest,
    InvocationResponse,
    InvocationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
executor = AgentExecutor()


@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_agent(request: DeploymentRequest):
    try:
        deployment_id = str(uuid.uuid4())
        code_hash = hash(request.code)
        resource_limits = {
            "max_memory": request.max_memory,
            "max_cpu": request.max_cpu
        }
        deployed_at = datetime.utcnow()
        
        query = """
        INSERT INTO agent_deployments 
        (id, agent_did, status, code, code_hash, resource_limits, deployed_at, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await db.execute(
            query,
            uuid.UUID(deployment_id),
            request.agent_id,
            AgentStatus.RUNNING.value,
            request.code,
            code_hash,
            resource_limits,
            deployed_at,
            {"requirements": request.requirements, "environment": request.environment}
        )
        
        logger.info(f"Deployed agent {request.agent_id} with deployment_id {deployment_id}")
        
        return DeploymentResponse(
            deployment_id=deployment_id,
            agent_id=request.agent_id,
            status=AgentStatus.RUNNING,
            container_id=None,
            endpoint=None,
            deployed_at=deployed_at,
            message="Agent deployed successfully"
        )
    except Exception as e:
        logger.error(f"Failed to deploy agent: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post("/invoke", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    try:
        deployment_query = """
        SELECT id, code FROM agent_deployments
        WHERE agent_did = $1 AND status = $2
        ORDER BY deployed_at DESC
        LIMIT 1
        """
        
        deployment = await db.fetchrow(
            deployment_query,
            request.agent_id,
            AgentStatus.RUNNING.value
        )
        
        if not deployment:
            raise HTTPException(status_code=404, detail=f"No running deployment found for agent {request.agent_id}")
        
        deployment_id = deployment['id']
        code = deployment['code']
        
        execution_result = await executor.execute(
            agent_id=request.agent_id,
            code=code,
            input_data=request.input_data,
            timeout=request.timeout
        )
        
        invocation_id = str(uuid.uuid4())
        input_hash = hashlib.sha256(str(request.input_data).encode()).hexdigest()
        output_hash = hashlib.sha256(str(execution_result['output']).encode()).hexdigest() if execution_result['output'] else None
        
        insert_query = """
        INSERT INTO agent_invocations
        (id, agent_did, deployment_id, input_hash, output_hash, status, 
         execution_time_ms, cost_cents, invoked_at, error_message)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        
        await db.execute(
            insert_query,
            uuid.UUID(invocation_id),
            request.agent_id,
            deployment_id,
            input_hash,
            output_hash,
            execution_result['status'],
            execution_result['execution_time_ms'],
            execution_result['cost_cents'],
            execution_result['invoked_at'],
            execution_result['error']
        )
        
        logger.info(f"Invoked agent {request.agent_id}, invocation_id {invocation_id}, status {execution_result['status']}")
        
        return InvocationResponse(
            invocation_id=invocation_id,
            agent_id=request.agent_id,
            status=InvocationStatus[execution_result['status']],
            output=execution_result['output'],
            error=execution_result['error'],
            execution_time_ms=execution_result['execution_time_ms'],
            cost_cents=execution_result['cost_cents'],
            invoked_at=execution_result['invoked_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invoke agent: {e}")
        raise HTTPException(status_code=500, detail=f"Invocation failed: {str(e)}")


@router.get("/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str):
    try:
        deployment_query = """
        SELECT status, container_id, deployed_at
        FROM agent_deployments
        WHERE agent_did = $1
        ORDER BY deployed_at DESC
        LIMIT 1
        """
        
        deployment = await db.fetchrow(deployment_query, agent_id)
        
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        invocations_query = """
        SELECT COUNT(*) as count, MAX(invoked_at) as last_invocation
        FROM agent_invocations
        WHERE agent_did = $1
        """
        
        invocations = await db.fetchrow(invocations_query, agent_id)
        
        return AgentStatusResponse(
            agent_id=agent_id,
            status=AgentStatus(deployment['status']),
            container_id=deployment['container_id'],
            deployed_at=deployment['deployed_at'],
            last_invocation=invocations['last_invocation'] if invocations else None,
            invocation_count=invocations['count'] if invocations else 0,
            cpu_percent=None,
            memory_mb=None,
            uptime_seconds=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    try:
        update_query = """
        UPDATE agent_deployments
        SET status = $1, stopped_at = $2
        WHERE agent_did = $3 AND status = $4
        """
        
        result = await db.execute(
            update_query,
            AgentStatus.TERMINATED.value,
            datetime.utcnow(),
            agent_id,
            AgentStatus.RUNNING.value
        )
        
        logger.info(f"Terminated agent {agent_id}")
        
        return {"deleted": True}
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
