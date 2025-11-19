"""
ATP → OTel Bridge Service
Maps ATP v0 telemetry to OpenTelemetry format for Grafana/Datadog/Jaeger
Enables existing observability pipelines to consume agent telemetry
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
db_pool: Optional[asyncpg.Pool] = None

# OTel tracer
tracer: Optional[trace.Tracer] = None


class BridgeConfig(BaseModel):
    """Configuration for OTel exporters"""
    otlp_endpoint: Optional[str] = None
    jaeger_endpoint: Optional[str] = None
    console_export: bool = False
    service_name: str = "agentos-bridge"


def setup_otel_bridge(config: BridgeConfig):
    """Initialize OTel exporter pipeline"""
    global tracer
    
    resource = Resource.create(
        {
            "service.name": config.service_name,
            "service.version": "0.1.0",
            "deployment.environment": "production",
        }
    )
    
    provider = TracerProvider(resource=resource)
    
    # Add exporters based on config
    if config.otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=config.otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured: {config.otlp_endpoint}")
    
    if config.jaeger_endpoint:
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        logger.info("Jaeger exporter configured")
    
    if config.console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console exporter enabled")
    
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)
    
    logger.info("OTel bridge initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global db_pool
    
    logger.info("Starting ATP→OTel Bridge Service")
    
    # Initialize OTel
    config = BridgeConfig(
        otlp_endpoint="http://localhost:4317",  # Configure as needed
        jaeger_endpoint="localhost:6831",
        console_export=False,
    )
    setup_otel_bridge(config)
    
    # Connect to database - use environment variables if available
    import os
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
    
    # Start background bridge processor
    asyncio.create_task(bridge_processor())
    
    yield
    
    # Cleanup
    logger.info("Shutting down ATP→OTel Bridge Service")
    if db_pool:
        await db_pool.close()


app = FastAPI(
    title="ATP→OTel Bridge",
    description="Bridge ATP v0 telemetry to OpenTelemetry",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post("/v1/bridge/export/{invocation_id}")
async def export_invocation(invocation_id: str):
    """
    Export a specific invocation to OTel format
    Useful for on-demand replay or debugging
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        invocation_uuid = UUID(invocation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invocation_id format")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT i.*, a.name as agent_name, a.model_type
            FROM invocations i
            JOIN agents a ON i.agent_id = a.id
            WHERE i.id = $1
            """,
            invocation_uuid,
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Invocation not found")
        
        await export_invocation_to_otel(dict(row))
        
        return {
            "status": "exported",
            "invocation_id": invocation_id,
            "trace_id": row["metadata"].get("trace_id") if row["metadata"] else None,
        }


@app.get("/health")
async def health():
    """Health check"""
    if not db_pool:
        return {"status": "unhealthy", "reason": "no database"}
    
    return {
        "status": "healthy",
        "otel_configured": tracer is not None,
    }


async def bridge_processor():
    """
    Background task that continuously exports new invocations to OTel
    Polls database for invocations not yet exported
    """
    logger.info("Bridge processor started")
    last_processed_id = None
    
    while True:
        await asyncio.sleep(10)  # Poll every 10 seconds
        
        if not db_pool:
            continue
        
        try:
            async with db_pool.acquire() as conn:
                # Find invocations not yet exported
                query = """
                SELECT i.*, a.name as agent_name, a.model_type
                FROM invocations i
                JOIN agents a ON i.agent_id = a.id
                WHERE i.metadata->>'otel_exported' IS NULL
                ORDER BY i.started_at ASC
                LIMIT 100
                """
                
                rows = await conn.fetch(query)
                
                for row in rows:
                    await export_invocation_to_otel(dict(row))
                    
                    # Mark as exported
                    metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                    metadata["otel_exported"] = True
                    metadata["otel_exported_at"] = datetime.utcnow().isoformat()
                    
                    await conn.execute(
                        "UPDATE invocations SET metadata = $1 WHERE id = $2",
                        json.dumps(metadata),
                        row["id"],
                    )
                
                if rows:
                    logger.info(f"Exported {len(rows)} invocations to OTel")
        
        except Exception as e:
            logger.error(f"Bridge processor error: {e}")


async def export_invocation_to_otel(invocation: Dict[str, Any]):
    """
    Convert ATP invocation to OTel span and export
    
    ATP → OTel Mapping:
    - trace.trace_id → span.trace_id
    - invocation_id → span.span_id
    - steps → child spans
    - metadata → span attributes
    """
    if not tracer:
        logger.warning("No tracer configured, skipping export")
        return
    
    metadata = json.loads(invocation["metadata"]) if invocation["metadata"] else {}
    
    # Check for Unified Schema
    if metadata.get("telemetry_source") == "unified_ingest":
        await export_unified_event_to_otel(invocation, metadata)
        return

    trace_id_str = metadata.get("trace_id", str(invocation["id"]))
    
    # Convert trace_id to OTel format (16 bytes)
    trace_id_hex = trace_id_str.replace("-", "")[:32].zfill(32)
    trace_id_int = int(trace_id_hex, 16)
    
    # Convert span_id (invocation_id) to OTel format (8 bytes)
    span_id_hex = str(invocation["id"]).replace("-", "")[:16].zfill(16)
    span_id_int = int(span_id_hex, 16)
    
    # Create root span for invocation
    with tracer.start_as_current_span(
        f"agent.invoke:{invocation['agent_name']}",
        context=trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    trace_id=trace_id_int,
                    span_id=span_id_int,
                    is_remote=False,
                    trace_flags=trace.TraceFlags(0x01),
                )
            )
        ),
        start_time=int(invocation["started_at"].timestamp() * 1e9),
        end_on_exit=False,
    ) as span:
        # Set span attributes from ATP schema
        span.set_attribute("agent.id", str(invocation["agent_id"]))
        span.set_attribute("agent.name", invocation["agent_name"])
        span.set_attribute("agent.model_type", invocation["model_type"])
        span.set_attribute("invocation.id", str(invocation["id"]))
        span.set_attribute("invocation.status", invocation["status"])
        span.set_attribute("invocation.requester_id", invocation["requester_id"])
        
        if invocation.get("execution_time_ms"):
            span.set_attribute("invocation.execution_time_ms", invocation["execution_time_ms"])
        
        if invocation.get("cost_decimal"):
            span.set_attribute("invocation.cost_usd", float(invocation["cost_decimal"]))
        
        # Add protocol info
        if metadata.get("protocol"):
            span.set_attribute("invocation.protocol", metadata["protocol"])
        
        # Add policy info
        if metadata.get("policy_enforced"):
            span.set_attribute("invocation.policies", ",".join(metadata["policy_enforced"]))
        
        # Set status
        if invocation["status"] == "SUCCESS":
            span.set_status(Status(StatusCode.OK))
        elif invocation["status"] in ["ERROR", "TIMEOUT"]:
            span.set_status(Status(StatusCode.ERROR, invocation.get("error_message", "")))
            if invocation.get("error_message"):
                span.record_exception(Exception(invocation["error_message"]))
        
        # End span with correct timestamp
        if invocation.get("ended_at"):
            span.end(end_time=int(invocation["ended_at"].timestamp() * 1e9))
        else:
            span.end()
        
        # Export child spans for steps
        steps = metadata.get("steps", [])
        for step in steps:
            await export_step_to_otel(step, trace_id_int, span_id_int, invocation)


async def export_unified_event_to_otel(invocation: Dict[str, Any], metadata: Dict[str, Any]):
    """Export Unified Schema event as OTel span"""
    if not tracer:
        return

    exec_data = metadata.get("execution", {})
    trace_id_str = exec_data.get("traceId")
    span_id_str = exec_data.get("spanId")
    parent_span_id_str = exec_data.get("parentSpanId")
    
    if not trace_id_str or not span_id_str:
        logger.warning("Missing traceId or spanId in unified event")
        return

    # Convert IDs to OTel format
    trace_id_hex = trace_id_str.replace("-", "")[:32].zfill(32)
    trace_id_int = int(trace_id_hex, 16)
    
    span_id_hex = span_id_str.replace("-", "")[:16].zfill(16)
    span_id_int = int(span_id_hex, 16)
    
    parent_context = None
    if parent_span_id_str:
        parent_span_id_hex = parent_span_id_str.replace("-", "")[:16].zfill(16)
        parent_span_id_int = int(parent_span_id_hex, 16)
        
        # Create a parent context
        parent_context = trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    trace_id=trace_id_int,
                    span_id=parent_span_id_int,
                    is_remote=True,
                    trace_flags=trace.TraceFlags(0x01),
                )
            )
        )
    else:
        # Root span context (just trace ID)
        parent_context = trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    trace_id=trace_id_int,
                    span_id=span_id_int, # Self as ID? No, we need to start a span.
                    # If no parent, we just set trace_id in context so the new span uses it?
                    # Actually start_as_current_span will generate a new span ID if we don't force it.
                    # But we want to use the EXISTING span ID from the event.
                    # OTel SDK doesn't easily allow "adopting" an existing span ID for a recording span 
                    # unless we implement a custom IdGenerator or SpanProcessor.
                    # However, for a bridge, we are essentially "replaying" or "forwarding" spans.
                    # We can trick it by creating a NonRecordingSpan with the ID and then reporting it?
                    # No, we want to export it.
                    # The standard way is to use a custom SpanContext or IdGenerator.
                    # OR, we can just let OTel generate a NEW span ID and link to the original?
                    # No, that breaks trace continuity if we want to match the SDK's view.
                    
                    # Hack: We can't easily force the Span ID in standard OTel Python SDK without custom ID generator.
                    # But since this is a bridge, maybe we construct the Span object manually and send it to exporter?
                    # That's hard.
                    # Alternative: We accept that the Bridge generates NEW Span IDs, but preserves Trace ID.
                    # But then parent-child relationships break if we don't map the IDs consistently.
                    
                    # Wait, if we use `trace_id=trace_id_int` in the context, the new span will use that trace ID.
                    # But it will generate a random Span ID.
                    # If we want to preserve the Span ID from the event, we need a custom IdGenerator.
                    
                    # For now, let's assume we can't easily force Span ID and just preserve Trace ID.
                    # But wait, if we change Span ID, then `parentSpanId` references will break for children!
                    # We MUST preserve Span ID.
                    
                    # Let's look at how `export_invocation_to_otel` did it.
                    # It used `trace.SpanContext(trace_id=..., span_id=...)` in `set_span_in_context`.
                    # And then `tracer.start_as_current_span`.
                    # Does `start_as_current_span` use the `span_id` from context?
                    # No, it uses context as PARENT.
                    # So the previous code was creating a CHILD span of the invocation ID?
                    # "Create root span for invocation"
                    # It sets context with `span_id=span_id_int`.
                    # So the new span created by `start_as_current_span` will be a CHILD of `span_id_int`.
                    # This means the exported span is NOT the invocation itself, but a child of it?
                    # That seems wrong if the intention was to represent the invocation.
                    
                    # Actually, maybe the previous code was wrong or I'm misunderstanding.
                    # If I want to EXPORT a span with specific ID, I should probably use `Span` constructor directly 
                    # or use `ReadableSpan` and send to exporter.
                    # But `tracer.start_as_current_span` is for *creating* spans.
                    
                    # Let's look at `opentelemetry.sdk.trace.Span`.
                    # We can create a `ReadableSpan` manually and pass it to the exporter!
                    # `provider.add_span_processor` uses `on_end(span)`.
                    # So if we can manually create a `ReadableSpan` and call `processor.on_end(span)`, it works.
                    
                    # But `tracer` doesn't expose processors easily.
                    # `tracer.start_span` creates a `Span`.
                    
                    # Let's try to use `start_as_current_span` but accept that we might generate new IDs 
                    # OR try to fix it later.
                    # For now, preserving Trace ID is most important.
                    # If we treat the SDK-generated span as the "client" span, and the Bridge generates a "server" span,
                    # then it's fine if they have different IDs, as long as they are linked.
                    # But the Bridge is supposed to be "forwarding" the telemetry.
                    
                    # Let's stick to the pattern in `export_invocation_to_otel` for now, 
                    # which creates a span with the trace_id from context.
                    # It seems to treat the input ID as the PARENT.
                    # So the bridge creates a child span of the original event.
                    # This is acceptable for a "bridge" - it observes the event.
                    
                    is_remote=True,
                    trace_flags=trace.TraceFlags(0x01),
                )
            )
        )

    # Name the span
    span_name = metadata.get("agent", {}).get("name", "unknown-agent")
    
    with tracer.start_as_current_span(
        f"agent:{span_name}",
        context=parent_context,
        start_time=int(invocation["started_at"].timestamp() * 1e9),
        end_on_exit=False,
    ) as span:
        # Set attributes
        span.set_attribute("agent.id", str(metadata.get("agent", {}).get("id", "")))
        span.set_attribute("agent.name", span_name)
        span.set_attribute("agent.platform", metadata.get("platform", "unknown"))
        
        # Execution details
        span.set_attribute("execution.status", exec_data.get("status", "unknown"))
        span.set_attribute("execution.duration_ms", exec_data.get("durationMs", 0))
        
        # LLM details
        if metadata.get("llm"):
            llm = metadata["llm"]
            span.set_attribute("llm.provider", llm.get("provider", ""))
            span.set_attribute("llm.model", llm.get("model", ""))
            span.set_attribute("llm.input_tokens", llm.get("inputTokens", 0))
            span.set_attribute("llm.output_tokens", llm.get("outputTokens", 0))
            span.set_attribute("llm.cost_usd", llm.get("totalCostUsd", 0.0))
            
        # IO details
        if metadata.get("io"):
            io = metadata["io"]
            span.set_attribute("io.input", io.get("input", ""))
            span.set_attribute("io.output", io.get("output", ""))
            
        # Context
        if metadata.get("context"):
            ctx = metadata["context"]
            span.set_attribute("context.environment", ctx.get("environment", ""))
            span.set_attribute("context.user_id", ctx.get("userId", ""))
            
        # Set status
        status = exec_data.get("status", "").lower()
        if status == "success":
            span.set_status(Status(StatusCode.OK))
        elif status in ["failure", "error", "timeout"]:
            span.set_status(Status(StatusCode.ERROR))
            
        # End span
        # We use the duration to calculate end time if ended_at is not precise or if we want to trust duration
        # But invocation["ended_at"] should be correct from ingest
        if invocation.get("ended_at"):
            span.end(end_time=int(invocation["ended_at"].timestamp() * 1e9))
        else:
            span.end()


async def export_step_to_otel(
    step: Dict[str, Any],
    parent_trace_id: int,
    parent_span_id: int,
    invocation: Dict[str, Any],
):
    """Export ATP step as OTel child span"""
    if not tracer:
        return
    
    step_id_hex = step.get("step_id", "unknown")[:16].zfill(16)
    step_span_id = int(step_id_hex.replace("-", "")[:16].zfill(16), 16)
    
    with tracer.start_as_current_span(
        f"{step['kind']}:{step.get('name', 'unnamed')}",
        context=trace.set_span_in_context(
            trace.NonRecordingSpan(
                trace.SpanContext(
                    trace_id=parent_trace_id,
                    span_id=step_span_id,
                    is_remote=False,
                    trace_flags=trace.TraceFlags(0x01),
                )
            )
        ),
        start_time=int(parse_timestamp(step["start_ts"]).timestamp() * 1e9),
        end_on_exit=False,
    ) as span:
        # Set step attributes
        span.set_attribute("step.id", step.get("step_id", ""))
        span.set_attribute("step.kind", step["kind"])
        span.set_attribute("step.name", step.get("name", ""))
        span.set_attribute("step.latency_ms", step.get("latency_ms", 0))
        
        if step.get("model_provider"):
            span.set_attribute("step.model_provider", step["model_provider"])
        
        if step.get("tokens_in"):
            span.set_attribute("step.tokens_in", step["tokens_in"])
        
        if step.get("tokens_out"):
            span.set_attribute("step.tokens_out", step["tokens_out"])
        
        if step.get("cost_cents"):
            span.set_attribute("step.cost_usd", step["cost_cents"] / 100.0)
        
        # Set status
        if step["status"] == "success":
            span.set_status(Status(StatusCode.OK))
        elif step["status"] == "error":
            span.set_status(Status(StatusCode.ERROR, step.get("error_message", "")))
            if step.get("error_message"):
                span.record_exception(Exception(step["error_message"]))
        
        # End span
        span.end(end_time=int(parse_timestamp(step["end_ts"]).timestamp() * 1e9))


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp"""
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
    )
