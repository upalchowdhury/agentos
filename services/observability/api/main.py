"""
Trace Explorer & Observability API
Provides REST endpoints for trace visualization, logs correlation, and metrics
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database pool
db_pool: Optional[asyncpg.Pool] = None


class TraceStep(BaseModel):
    """Step within a trace"""
    step_id: str
    parent_step_id: Optional[str]
    name: str
    kind: str
    start_ts: str
    end_ts: str
    latency_ms: int
    status: str
    model_provider: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_cents: Optional[int] = None
    error_message: Optional[str] = None
    input_excerpt: Optional[str] = None
    output_excerpt: Optional[str] = None


class TraceDetail(BaseModel):
    """Complete trace with steps"""
    trace_id: str
    invocation_id: str
    agent_id: str
    agent_name: str
    status: str
    start_ts: str
    end_ts: str
    execution_time_ms: int
    cost_usd: float
    protocol: Optional[str] = None
    policy_enforced: List[str] = []
    signature_verified: bool = False
    error_message: Optional[str] = None
    steps: List[TraceStep] = []


class LogEntry(BaseModel):
    """Log entry correlated to trace"""
    timestamp: str
    level: str
    message: str
    step_id: Optional[str] = None
    trace_id: Optional[str] = None


class InvocationSummary(BaseModel):
    """Summary of an invocation for list views"""
    invocation_id: str
    trace_id: Optional[str]
    agent_id: str
    agent_name: str
    status: str
    started_at: str
    execution_time_ms: Optional[int]
    cost_usd: Optional[float]


class MetricsSummary(BaseModel):
    """Aggregated metrics for an agent"""
    agent_id: str
    agent_name: str
    total_invocations: int
    successful_invocations: int
    failed_invocations: int
    avg_execution_time_ms: Optional[float]
    p50_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    p99_latency_ms: Optional[float]
    total_cost_usd: Optional[float]
    last_invoked_at: Optional[str]


async def init_db():
    """Initialize database connection"""
    global db_pool
    
    import os
    
    # Use environment variables if available
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = int(os.getenv("DATABASE_PORT", "5432"))
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_password = os.getenv("DATABASE_PASSWORD", "postgres")
    db_name = os.getenv("DATABASE_NAME", "agentos")
    
    logger.info(f"Connecting to database: {db_user}@{db_host}:{db_port}/{db_name}")
    
    db_pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        min_size=2,
        max_size=10,
    )
    logger.info("Database pool initialized")


app = FastAPI(
    title="Observability API",
    description="Trace explorer and metrics API for AgentOS",
    version="0.1.0",
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()


@app.get("/v1/traces/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: str):
    """
    Get complete trace with all steps
    US-O2: Trace explorer with step-level detail
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # Find invocation by trace_id
        row = await conn.fetchrow(
            """
            SELECT i.*, a.name as agent_name
            FROM invocations i
            JOIN agents a ON i.agent_id = a.id
            WHERE i.metadata->>'trace_id' = $1
            ORDER BY i.started_at DESC
            LIMIT 1
            """,
            trace_id,
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        steps_data = metadata.get("steps", [])
        
        # Parse steps
        steps = []
        for step in steps_data:
            if isinstance(step, dict):
                steps.append(TraceStep(**step))
        
        return TraceDetail(
            trace_id=trace_id,
            invocation_id=str(row["id"]),
            agent_id=str(row["agent_id"]),
            agent_name=row["agent_name"],
            status=row["status"],
            start_ts=row["started_at"].isoformat(),
            end_ts=row["ended_at"].isoformat() if row["ended_at"] else "",
            execution_time_ms=row["execution_time_ms"] or 0,
            cost_usd=float(row["cost_decimal"]) if row["cost_decimal"] else 0.0,
            protocol=metadata.get("protocol"),
            policy_enforced=metadata.get("policy_enforced", []),
            signature_verified=metadata.get("signature_verified", False),
            error_message=row["error_message"],
            steps=steps,
        )


@app.get("/v1/traces", response_model=List[InvocationSummary])
async def list_traces(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = Query(default=50, le=1000),
):
    """
    List traces with filtering
    US-O1: Org/Project dashboards
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Build query
    conditions = []
    params = []
    param_idx = 1
    
    if agent_id:
        try:
            agent_uuid = UUID(agent_id)
            conditions.append(f"i.agent_id = ${param_idx}")
            params.append(agent_uuid)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id format")
    
    if status:
        conditions.append(f"i.status = ${param_idx}")
        params.append(status.upper())
        param_idx += 1
    
    if start_time:
        conditions.append(f"i.started_at >= ${param_idx}")
        params.append(datetime.fromisoformat(start_time))
        param_idx += 1
    
    if end_time:
        conditions.append(f"i.started_at <= ${param_idx}")
        params.append(datetime.fromisoformat(end_time))
        param_idx += 1
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    query = f"""
    SELECT i.id, i.agent_id, i.status, i.started_at, 
           i.execution_time_ms, i.cost_decimal, i.metadata,
           a.name as agent_name
    FROM invocations i
    JOIN agents a ON i.agent_id = a.id
    WHERE {where_clause}
    ORDER BY i.started_at DESC
    LIMIT {limit}
    """
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        
        results = []
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            
            results.append(InvocationSummary(
                invocation_id=str(row["id"]),
                trace_id=metadata.get("trace_id"),
                agent_id=str(row["agent_id"]),
                agent_name=row["agent_name"],
                status=row["status"],
                started_at=row["started_at"].isoformat(),
                execution_time_ms=row["execution_time_ms"],
                cost_usd=float(row["cost_decimal"]) if row["cost_decimal"] else None,
            ))
        
        return results


@app.get("/v1/logs", response_model=List[LogEntry])
async def get_logs(
    trace_id: Optional[str] = None,
    invocation_id: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
):
    """
    Get logs correlated by trace_id
    US-O2: Logs correlation
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    if not trace_id and not invocation_id:
        raise HTTPException(
            status_code=400,
            detail="Either trace_id or invocation_id required",
        )
    
    async with db_pool.acquire() as conn:
        if invocation_id:
            try:
                inv_uuid = UUID(invocation_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid invocation_id")
            
            row = await conn.fetchrow(
                "SELECT metadata FROM invocations WHERE id = $1",
                inv_uuid,
            )
        else:
            row = await conn.fetchrow(
                "SELECT metadata FROM invocations WHERE metadata->>'trace_id' = $1 LIMIT 1",
                trace_id,
            )
        
        if not row:
            return []
        
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        logs = metadata.get("logs", [])
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.get("level") == level.upper()]
        
        # Limit results
        logs = logs[:limit]
        
        return [LogEntry(**log) for log in logs if isinstance(log, dict)]


@app.get("/v1/agents/{agent_id}/metrics", response_model=MetricsSummary)
async def get_agent_metrics(agent_id: str):
    """
    Get aggregated metrics for an agent
    US-O1: Dashboard metrics
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        agent_uuid = UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM agent_stats_v2 WHERE agent_id = $1",
            agent_uuid,
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return MetricsSummary(
            agent_id=str(row["agent_id"]),
            agent_name=row["name"],
            total_invocations=row["total_invocations"] or 0,
            successful_invocations=row["successful_invocations"] or 0,
            failed_invocations=row["failed_invocations"] or 0,
            avg_execution_time_ms=float(row["avg_execution_time_ms"]) if row["avg_execution_time_ms"] else None,
            p50_latency_ms=float(row["p50_latency_ms"]) if row["p50_latency_ms"] else None,
            p95_latency_ms=float(row["p95_latency_ms"]) if row["p95_latency_ms"] else None,
            p99_latency_ms=float(row["p99_latency_ms"]) if row["p99_latency_ms"] else None,
            total_cost_usd=float(row["total_cost_usd"]) if row["total_cost_usd"] else None,
            last_invoked_at=row["last_invoked_at"].isoformat() if row["last_invoked_at"] else None,
        )


@app.get("/v1/cost/summary")
async def get_cost_summary(
    agent_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    period_days: int = Query(default=30, le=365),
):
    """
    Get cost summary aggregated by period
    US-A3: Cost attribution
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    conditions = []
    params = []
    param_idx = 1
    
    if agent_id:
        try:
            agent_uuid = UUID(agent_id)
            conditions.append(f"agent_id = ${param_idx}")
            params.append(agent_uuid)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id")
    
    if owner_id:
        conditions.append(f"owner_id = ${param_idx}")
        params.append(owner_id)
        param_idx += 1
    
    # Add time filter
    start_date = datetime.utcnow() - timedelta(days=period_days)
    conditions.append(f"period_start >= ${param_idx}")
    params.append(start_date)
    param_idx += 1
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    query = f"""
    SELECT 
        SUM(total_invocations) as total_invocations,
        SUM(successful_invocations) as successful_invocations,
        SUM(failed_invocations) as failed_invocations,
        SUM(total_cost) as total_cost,
        SUM(compute_cost) as compute_cost,
        SUM(llm_api_cost) as llm_api_cost
    FROM cost_snapshots
    WHERE {where_clause}
    """
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(query, *params)
        
        return {
            "period_days": period_days,
            "total_invocations": row["total_invocations"] or 0,
            "successful_invocations": row["successful_invocations"] or 0,
            "failed_invocations": row["failed_invocations"] or 0,
            "total_cost_usd": float(row["total_cost"]) if row["total_cost"] else 0.0,
            "compute_cost_usd": float(row["compute_cost"]) if row["compute_cost"] else 0.0,
            "llm_api_cost_usd": float(row["llm_api_cost"]) if row["llm_api_cost"] else 0.0,
        }


@app.get("/health")
async def health():
    """Health check"""
    if not db_pool:
        return {"status": "unhealthy", "reason": "no database"}
    
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )
