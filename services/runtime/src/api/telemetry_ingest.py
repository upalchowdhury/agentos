"""
Telemetry ingest endpoint for Model B agents using SDK.
Receives ATP v0 traces and stores them in the database.
"""

import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..database import db
from .agents_v2 import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/telemetry", tags=["telemetry"])


class TelemetryIngestRequest(BaseModel):
    """Request model for telemetry ingest"""
    trace: Dict[str, Any] = Field(..., description="ATP v0 trace data")
    telemetry_quality: str = Field(default="verified", description="Telemetry quality badge")


@router.post("/ingest")
async def ingest_telemetry(
    request: TelemetryIngestRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Ingest ATP v0 telemetry from external agents (Model B).
    
    This endpoint allows agents using the Python/TypeScript SDK to send
    step-level traces. Marks invocations with 'verified' telemetry quality.
    
    Returns:
        Status of ingestion and invocation_id for tracking
    """
    trace = request.trace
    
    # Validate required ATP v0 fields
    required_fields = [
        "trace_id", "invocation_id", "agent_id", 
        "status", "start_ts", "end_ts", "execution_time_ms"
    ]
    missing = [f for f in required_fields if f not in trace]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required ATP v0 fields: {', '.join(missing)}"
        )
    
    # Extract fields
    trace_id = trace["trace_id"]
    invocation_id = trace["invocation_id"]
    agent_id_str = trace["agent_id"]
    status = trace["status"].upper()
    
    # Parse timestamps
    try:
        start_ts = _parse_timestamp(trace["start_ts"])
        end_ts = _parse_timestamp(trace["end_ts"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {e}")
    
    execution_time_ms = int(trace.get("execution_time_ms", 0))
    cost_cents = int(trace.get("cost_cents", 0))
    cost_decimal = Decimal(cost_cents) / Decimal(100)
    error_message = trace.get("error_message")
    
    # Verify agent exists and user has access
    try:
        agent_uuid = uuid.UUID(agent_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")
    
    agent = await db.fetchrow(
        "SELECT id, owner_id, name FROM agents WHERE id = $1",
        agent_uuid
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if str(agent["owner_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Access denied to agent")
    
    # Build metadata with trace and telemetry quality
    steps = trace.get("steps", [])
    logs = _extract_logs_from_steps(steps)
    
    metadata = {
        "trace": {
            "trace_id": trace_id,
            "start_ts": trace["start_ts"],
            "end_ts": trace["end_ts"],
            "execution_time_ms": execution_time_ms,
            "steps": steps,
            "logs": logs,
        },
        "telemetry_quality": request.telemetry_quality,
        "source": "sdk_ingest",
        "sdk_version": trace.get("sdk_version", "unknown"),
    }
    
    # Store invocation
    try:
        invocation_uuid = uuid.UUID(invocation_id) if "-" in invocation_id else uuid.uuid4()
    except ValueError:
        invocation_uuid = uuid.uuid4()
    
    await db.execute(
        """
        INSERT INTO invocations (
            id, agent_id, requester_id, status, started_at, ended_at,
            execution_time_ms, cost_decimal, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO UPDATE SET
            status = EXCLUDED.status,
            ended_at = EXCLUDED.ended_at,
            execution_time_ms = EXCLUDED.execution_time_ms,
            cost_decimal = EXCLUDED.cost_decimal,
            metadata = EXCLUDED.metadata
        """,
        invocation_uuid,
        agent_uuid,
        user_id,
        status,
        start_ts,
        end_ts,
        execution_time_ms,
        cost_decimal,
        json.dumps(metadata),
    )
    
    logger.info(
        f"Telemetry ingested for agent {agent_id_str}: "
        f"trace_id={trace_id}, status={status}, steps={len(steps)}"
    )
    
    return {
        "status": "success",
        "invocation_id": str(invocation_uuid),
        "trace_id": trace_id,
        "agent_name": agent["name"],
        "telemetry_quality": request.telemetry_quality,
        "steps_ingested": len(steps),
    }


def _parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp"""
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid ISO 8601 timestamp: {ts_str}") from e


def _extract_logs_from_steps(steps: list) -> list:
    """Convert steps to log entries for correlation"""
    logs = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        
        level = "ERROR" if step.get("status") == "error" else "INFO"
        message = f"{step.get('kind', 'step')}: {step.get('name', 'unnamed')}"
        
        if step.get("error_message"):
            message += f" - {step.get('error_message')}"
        
        logs.append({
            "timestamp": step.get("start_ts"),
            "level": level,
            "message": message,
            "step_id": step.get("step_id"),
            "latency_ms": step.get("latency_ms"),
        })
    
    return logs
