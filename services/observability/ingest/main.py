"""
ATP v0 Ingest Service
Receives telemetry events from agents and stores them in ClickHouse/Postgres
Handles high-throughput bursts (500 RPS target) with batching
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database pool
db_pool: Optional[asyncpg.Pool] = None

# Batch buffer for high throughput
event_buffer: List[Dict[str, Any]] = []
BATCH_SIZE = 100
BATCH_TIMEOUT = 5.0  # seconds


class ATPTrace(BaseModel):
    """ATP v0 Trace Schema"""
    trace_id: str
    invocation_id: str
    org_id: Optional[str] = None
    project_id: Optional[str] = None
    agent_id: str
    version_id: Optional[str] = None
    protocol: str = "http"
    policy_enforced: List[str] = Field(default_factory=list)
    signature_verified: bool = False
    provider_adapter: Optional[str] = None
    start_ts: str
    end_ts: str
    status: str
    execution_time_ms: int
    cost_cents: int = 0
    error_message: Optional[str] = None


class ATPStep(BaseModel):
    """ATP v0 Step Schema"""
    step_id: str
    parent_step_id: Optional[str] = None
    name: str
    kind: str  # prompt|tool|subagent|system
    start_ts: str
    end_ts: str
    latency_ms: int
    gateway_latency_ms: Optional[int] = None
    model_provider: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_cents: Optional[int] = None
    redaction_applied: bool = False
    budget_enforced_cents: Optional[int] = None
    status: str
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input_excerpt: Optional[str] = None
    output_excerpt: Optional[str] = None


class ATPEvent(BaseModel):
    """Complete ATP v0 Event"""
    trace: ATPTrace
    steps: List[ATPStep] = Field(default_factory=list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global db_pool
    
    import os
    
    logger.info("Initializing ATP Ingest Service")
    
    # Initialize database pool - use environment variables if available
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
        min_size=5,
        max_size=20,
        command_timeout=5.0,
    )
    
    logger.info("Database pool initialized")
    
    # Start background batch processor
    asyncio.create_task(batch_processor())
    
    yield
    
    # Cleanup
    logger.info("Shutting down ATP Ingest Service")
    if db_pool:
        await db_pool.close()


app = FastAPI(
    title="ATP Ingest Service",
    description="High-throughput telemetry ingest for AgentOS",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post("/v1/telemetry/events")
async def ingest_event(event: ATPEvent, background_tasks: BackgroundTasks):
    """
    Ingest ATP v0 telemetry event
    Buffers events and writes in batches for performance
    
    Performance target: p95 < 200ms, sustain 500 RPS for 2 min
    """
    try:
        # Add to buffer
        event_buffer.append(event.model_dump())
        
        # If buffer is full, flush immediately
        if len(event_buffer) >= BATCH_SIZE:
            background_tasks.add_task(flush_buffer)
        
        return {
            "status": "accepted",
            "trace_id": event.trace.trace_id,
            "buffered_count": len(event_buffer),
        }
    
    except Exception as e:
        logger.error(f"Failed to buffer event: {e}")
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


@app.post("/v1/telemetry/batch")
async def ingest_batch(events: List[ATPEvent]):
    """
    Ingest multiple ATP events in a single request
    For SDK clients that batch locally
    """
    if not events:
        return {"status": "success", "count": 0}
    
    if len(events) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Batch size exceeds limit (1000 events)",
        )
    
    try:
        await write_events_to_db([e.model_dump() for e in events])
        
        return {
            "status": "success",
            "count": len(events),
            "trace_ids": [e.trace.trace_id for e in events],
        }
    
    except Exception as e:
        logger.error(f"Batch ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch ingest failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    if not db_pool:
        return {"status": "unhealthy", "reason": "no database connection"}
    
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        return {
            "status": "healthy",
            "buffer_size": len(event_buffer),
            "db_pool_size": db_pool.get_size(),
        }
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}


async def batch_processor():
    """Background task that periodically flushes the buffer"""
    while True:
        await asyncio.sleep(BATCH_TIMEOUT)
        
        if event_buffer:
            await flush_buffer()


async def flush_buffer():
    """Flush buffered events to database"""
    if not event_buffer:
        return
    
    # Grab current buffer and clear it
    events_to_write = event_buffer.copy()
    event_buffer.clear()
    
    try:
        await write_events_to_db(events_to_write)
        logger.info(f"Flushed {len(events_to_write)} events to database")
    except Exception as e:
        logger.error(f"Failed to flush buffer: {e}")
        # Could implement retry logic or DLQ here


async def write_events_to_db(events: List[Dict[str, Any]]):
    """Write events to database"""
    if not db_pool or not events:
        return
    
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            for event_data in events:
                trace = event_data["trace"]
                steps = event_data.get("steps", [])
                
                # Parse timestamps
                start_ts = parse_timestamp(trace["start_ts"])
                end_ts = parse_timestamp(trace["end_ts"])
                
                # Validate agent exists
                try:
                    agent_id = UUID(trace["agent_id"])
                except ValueError:
                    logger.warning(f"Invalid agent_id: {trace['agent_id']}")
                    continue
                
                agent = await conn.fetchrow(
                    "SELECT id FROM agents WHERE id = $1",
                    agent_id,
                )
                
                if not agent:
                    logger.warning(f"Agent not found: {agent_id}")
                    continue
                
                # Insert or update invocation
                try:
                    invocation_id = UUID(trace["invocation_id"])
                except ValueError:
                    logger.warning(f"Invalid invocation_id: {trace['invocation_id']}")
                    continue
                
                # Build metadata with trace and steps
                metadata = {
                    "trace_id": trace["trace_id"],
                    "protocol": trace["protocol"],
                    "policy_enforced": trace.get("policy_enforced", []),
                    "signature_verified": trace.get("signature_verified", False),
                    "provider_adapter": trace.get("provider_adapter"),
                    "steps": steps,
                    "telemetry_source": "atp_ingest",
                }
                
                # Get requester_id from trace or use default
                requester_id = trace.get("org_id") or trace.get("requester_id") or "atp-telemetry"
                
                await conn.execute(
                    """
                    INSERT INTO invocations (
                        id, agent_id, requester_id, status, 
                        started_at, ended_at, execution_time_ms,
                        cost_decimal, error_message, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        ended_at = EXCLUDED.ended_at,
                        execution_time_ms = EXCLUDED.execution_time_ms,
                        cost_decimal = EXCLUDED.cost_decimal,
                        error_message = EXCLUDED.error_message,
                        metadata = EXCLUDED.metadata
                    """,
                    invocation_id,
                    agent_id,
                    requester_id,
                    trace["status"].upper(),
                    start_ts,
                    end_ts,
                    trace["execution_time_ms"],
                    trace["cost_cents"] / 100.0,
                    trace.get("error_message"),
                    json.dumps(metadata),
                )


def parse_timestamp(ts_str: str) -> datetime:
    """Parse RFC3339/ISO 8601 timestamp"""
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    
    try:
        dt = datetime.fromisoformat(ts_str)
        # Remove timezone for postgres timestamp column
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid timestamp: {ts_str}") from e


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
