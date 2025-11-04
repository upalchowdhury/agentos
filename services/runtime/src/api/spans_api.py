"""
Span-level telemetry API for ATP v0.1.

Endpoints for ingesting, querying, and analyzing spans and edges.
Supports Model A (runtime) and Model B (SDK) telemetry.
"""

import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..database import db
from .agents_v2 import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/spans", tags=["spans"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SpanIngestRequest(BaseModel):
    """ATP v0.1 span ingest"""
    spans: List[Dict[str, Any]] = Field(..., description="List of span objects")
    trace_context: Optional[Dict[str, Any]] = Field(None, description="W3C trace context (traceparent, baggage)")


class EdgeIngestRequest(BaseModel):
    """Inter-agent edge ingest"""
    edges: List[Dict[str, Any]] = Field(..., description="List of edge objects")


class SpanQueryRequest(BaseModel):
    """Span query filters"""
    trace_id: Optional[str] = None
    invocation_id: Optional[str] = None
    agent_id: Optional[str] = None
    kind: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class AnomalyDetectionRequest(BaseModel):
    """Request anomaly detection on spans"""
    span_ids: Optional[List[str]] = None
    trace_id: Optional[str] = None
    agent_id: Optional[str] = None
    detectors: List[str] = Field(["all"], description="Detector names or 'all'")


# ============================================================================
# Ingest Endpoints
# ============================================================================

@router.post("/ingest")
async def ingest_spans(
    request: SpanIngestRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Ingest ATP v0.1 spans from Model A (runtime) or Model B (SDK).

    Validates spans, stores in telemetry_spans table, and creates span links.
    Also stores trace context for W3C propagation.
    """
    spans = request.spans
    trace_context = request.trace_context or {}

    if not spans:
        raise HTTPException(status_code=400, detail="No spans provided")

    # Extract trace_id from first span
    trace_id_str = spans[0].get("trace_id")
    if not trace_id_str:
        raise HTTPException(status_code=400, detail="Missing trace_id in spans")

    try:
        trace_uuid = uuid.UUID(trace_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trace_id format")

    # Store trace context if provided
    if trace_context:
        await _store_trace_context(trace_uuid, trace_context)

    # Ingest each span
    span_ids = []
    for span_data in spans:
        try:
            span_uuid = await _ingest_single_span(span_data, user_id)
            span_ids.append(str(span_uuid))

            # Create span links if present
            links = span_data.get("links", [])
            if links:
                await _create_span_links(span_uuid, links)

        except Exception as e:
            logger.error(f"Failed to ingest span: {e}", exc_info=True)
            # Continue ingesting other spans

    logger.info(
        f"Ingested {len(span_ids)} spans for trace {trace_id_str} by user {user_id}"
    )

    return {
        "status": "success",
        "trace_id": trace_id_str,
        "spans_ingested": len(span_ids),
        "span_ids": span_ids
    }


@router.post("/edges/ingest")
async def ingest_edges(
    request: EdgeIngestRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Ingest inter-agent edges for A2A/MCP flows.

    Edges represent message passing between agents and are used
    for sequence diagram visualization.
    """
    edges = request.edges

    if not edges:
        raise HTTPException(status_code=400, detail="No edges provided")

    edge_ids = []
    for edge_data in edges:
        try:
            edge_uuid = await _ingest_single_edge(edge_data, user_id)
            edge_ids.append(str(edge_uuid))
        except Exception as e:
            logger.error(f"Failed to ingest edge: {e}", exc_info=True)

    return {
        "status": "success",
        "edges_ingested": len(edge_ids),
        "edge_ids": edge_ids
    }


# ============================================================================
# Query Endpoints
# ============================================================================

@router.get("/trace/{trace_id}")
async def get_trace_spans(
    trace_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get all spans for a trace, organized hierarchically.

    Returns span tree suitable for flamegraph visualization.
    """
    try:
        trace_uuid = uuid.UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trace_id format")

    # Get spans using the span_tree view
    rows = await db.fetch(
        """
        SELECT
            span_id, parent_span_id, name, kind, start_ts, duration_ms,
            status, agent_id, depth, path
        FROM span_tree
        WHERE trace_id = $1
        ORDER BY path
        """,
        trace_uuid
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Trace not found")

    # Get full span details
    span_details = []
    for row in rows:
        span = await db.fetchrow(
            "SELECT * FROM telemetry_spans WHERE span_id = $1",
            row["span_id"]
        )
        if span:
            span_dict = dict(span)
            span_dict["depth"] = row["depth"]
            span_details.append(_serialize_span(span_dict))

    return {
        "trace_id": trace_id,
        "span_count": len(span_details),
        "spans": span_details
    }


@router.get("/{span_id}")
async def get_span(
    span_id: str,
    user_id: str = Depends(get_current_user),
):
    """Get detailed information for a single span"""
    try:
        span_uuid = uuid.UUID(span_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid span_id format")

    span = await db.fetchrow(
        "SELECT * FROM telemetry_spans WHERE span_id = $1",
        span_uuid
    )

    if not span:
        raise HTTPException(status_code=404, detail="Span not found")

    # Get span links
    links = await db.fetch(
        """
        SELECT linked_span_id, link_type, attributes
        FROM span_links
        WHERE span_id = $1
        """,
        span_uuid
    )

    # Get anomalies for this span
    anomalies = await db.fetch(
        """
        SELECT anomaly_type, severity, confidence, detector_name, evidence
        FROM span_anomalies
        WHERE span_id = $1 AND status = 'open'
        ORDER BY severity DESC, detected_at DESC
        """,
        span_uuid
    )

    span_dict = _serialize_span(dict(span))
    span_dict["links"] = [dict(link) for link in links]
    span_dict["anomalies"] = [dict(a) for a in anomalies]

    return span_dict


@router.post("/query")
async def query_spans(
    request: SpanQueryRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Query spans with filters.

    Supports filtering by trace, invocation, agent, kind, status, and time range.
    """
    conditions = []
    params = []
    param_idx = 1

    if request.trace_id:
        try:
            trace_uuid = uuid.UUID(request.trace_id)
            conditions.append(f"trace_id = ${param_idx}")
            params.append(trace_uuid)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trace_id")

    if request.invocation_id:
        try:
            inv_uuid = uuid.UUID(request.invocation_id)
            conditions.append(f"invocation_id = ${param_idx}")
            params.append(inv_uuid)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid invocation_id")

    if request.agent_id:
        try:
            agent_uuid = uuid.UUID(request.agent_id)
            conditions.append(f"agent_id = ${param_idx}")
            params.append(agent_uuid)
            param_idx += 1
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id")

    if request.kind:
        conditions.append(f"kind = ${param_idx}")
        params.append(request.kind)
        param_idx += 1

    if request.status:
        conditions.append(f"status = ${param_idx}")
        params.append(request.status)
        param_idx += 1

    if request.start_time:
        conditions.append(f"start_ts >= ${param_idx}")
        params.append(request.start_time)
        param_idx += 1

    if request.end_time:
        conditions.append(f"start_ts <= ${param_idx}")
        params.append(request.end_time)
        param_idx += 1

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM telemetry_spans WHERE {where_clause}"
    total = await db.fetchval(count_query, *params)

    # Get spans
    params.append(request.limit)
    params.append(request.offset)
    query = f"""
        SELECT * FROM telemetry_spans
        WHERE {where_clause}
        ORDER BY start_ts DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """

    rows = await db.fetch(query, *params)
    spans = [_serialize_span(dict(row)) for row in rows]

    return {
        "total": total,
        "limit": request.limit,
        "offset": request.offset,
        "spans": spans
    }


@router.get("/edges/trace/{trace_id}")
async def get_trace_edges(
    trace_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Get all inter-agent edges for a trace.

    Used for sequence diagram visualization of A2A/MCP flows.
    """
    try:
        trace_uuid = uuid.UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trace_id")

    rows = await db.fetch(
        """
        SELECT * FROM inter_agent_flows
        WHERE trace_id = $1
        ORDER BY timestamp ASC
        """,
        trace_uuid
    )

    edges = [_serialize_edge(dict(row)) for row in rows]

    return {
        "trace_id": trace_id,
        "edge_count": len(edges),
        "edges": edges
    }


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/stats/agent/{agent_id}")
async def get_agent_span_stats(
    agent_id: str,
    user_id: str = Depends(get_current_user),
):
    """Get span statistics per agent and kind"""
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id")

    rows = await db.fetch(
        """
        SELECT * FROM span_stats_per_agent
        WHERE agent_id = $1
        ORDER BY kind
        """,
        agent_uuid
    )

    stats = [dict(row) for row in rows]

    return {
        "agent_id": agent_id,
        "stats": stats
    }


@router.post("/anomalies/detect")
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Run anomaly detection on spans.

    Supports: prompt_injection, tool_abuse, cost_outlier, context_tampering
    """
    span_ids = request.span_ids or []
    trace_id = request.trace_id
    agent_id = request.agent_id

    # Build span selection
    if span_ids:
        span_uuids = [uuid.UUID(sid) for sid in span_ids]
        spans = await db.fetch(
            "SELECT * FROM telemetry_spans WHERE span_id = ANY($1)",
            span_uuids
        )
    elif trace_id:
        trace_uuid = uuid.UUID(trace_id)
        spans = await db.fetch(
            "SELECT * FROM telemetry_spans WHERE trace_id = $1",
            trace_uuid
        )
    elif agent_id:
        agent_uuid = uuid.UUID(agent_id)
        spans = await db.fetch(
            "SELECT * FROM telemetry_spans WHERE agent_id = $1 LIMIT 100",
            agent_uuid
        )
    else:
        raise HTTPException(status_code=400, detail="Must provide span_ids, trace_id, or agent_id")

    detectors = request.detectors
    if "all" in detectors:
        detectors = ["prompt_injection", "tool_abuse", "cost_outlier", "context_tampering"]

    anomalies_detected = []

    for span in spans:
        span_dict = dict(span)
        for detector in detectors:
            anomaly = await _run_detector(detector, span_dict)
            if anomaly:
                anomalies_detected.append(anomaly)

    return {
        "status": "success",
        "spans_analyzed": len(spans),
        "anomalies_detected": len(anomalies_detected),
        "anomalies": anomalies_detected
    }


@router.get("/anomalies/summary")
async def get_anomaly_summary(
    agent_id: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user),
):
    """Get anomaly summary by agent and type"""
    if agent_id:
        agent_uuid = uuid.UUID(agent_id)
        rows = await db.fetch(
            "SELECT * FROM anomaly_summary WHERE agent_id = $1",
            agent_uuid
        )
    else:
        rows = await db.fetch("SELECT * FROM anomaly_summary")

    return {
        "summary": [dict(row) for row in rows]
    }


# ============================================================================
# Internal Helper Functions
# ============================================================================

async def _ingest_single_span(span_data: Dict[str, Any], user_id: str) -> uuid.UUID:
    """Insert a single span into telemetry_spans table"""
    # Required fields
    span_id = span_data.get("span_id", str(uuid.uuid4()))
    trace_id = span_data["trace_id"]
    invocation_id = span_data["invocation_id"]
    agent_id = span_data["agent_id"]
    name = span_data["name"]
    kind = span_data["kind"]
    start_ts = _parse_timestamp(span_data["start_ts"])
    status = span_data.get("status", "success")

    # Optional fields
    parent_span_id = span_data.get("parent_span_id")
    version_id = span_data.get("version_id")
    end_ts = _parse_timestamp(span_data["end_ts"]) if span_data.get("end_ts") else None
    duration_ms = span_data.get("duration_ms")

    # Convert to UUIDs
    span_uuid = uuid.UUID(span_id) if "-" in span_id else uuid.uuid4()
    trace_uuid = uuid.UUID(trace_id)
    invocation_uuid = uuid.UUID(invocation_id) if "-" in invocation_id else uuid.uuid4()
    agent_uuid = uuid.UUID(agent_id)
    version_uuid = uuid.UUID(version_id) if version_id else None
    parent_span_uuid = uuid.UUID(parent_span_id) if parent_span_id else None

    # Model info
    model_provider = span_data.get("model_provider")
    model_name = span_data.get("model_name")
    model_params = span_data.get("model_params")

    # I/O
    tokens_in = span_data.get("tokens_in")
    tokens_out = span_data.get("tokens_out")
    input_excerpt = span_data.get("input_excerpt")
    output_excerpt = span_data.get("output_excerpt")
    content_hash_in = span_data.get("content_hash_in")
    content_hash_out = span_data.get("content_hash_out")
    signature_verified = span_data.get("signature_verified", False)

    # Tool info
    tool_call_id = span_data.get("tool_call_id")
    tool_name = span_data.get("tool_name")
    tool_args_excerpt = span_data.get("tool_args_excerpt")
    tool_return_excerpt = span_data.get("tool_return_excerpt")

    # Policy
    policy_enforced = span_data.get("policy_enforced", [])
    obligations = span_data.get("obligations", [])
    redaction_mask_ids = span_data.get("redaction_mask_ids", [])
    budget_enforced_cents = span_data.get("budget_enforced_cents")
    policy_allow = span_data.get("policy_allow", True)

    # Network
    protocol = span_data.get("protocol")
    remote_agent_id = span_data.get("remote_agent_id")
    remote_agent_uuid = uuid.UUID(remote_agent_id) if remote_agent_id else None
    remote_version_id = span_data.get("remote_version_id")
    remote_version_uuid = uuid.UUID(remote_version_id) if remote_version_id else None
    request_id = span_data.get("request_id")
    edge_id = span_data.get("edge_id")
    edge_uuid = uuid.UUID(edge_id) if edge_id else None

    # Cost & error
    cost_cents = span_data.get("cost_cents", 0)
    error_type = span_data.get("error_type")
    error_message = span_data.get("error_message")

    # Metadata
    metadata = span_data.get("metadata", {})

    # Insert span
    await db.execute(
        """
        INSERT INTO telemetry_spans (
            span_id, trace_id, parent_span_id, invocation_id, agent_id, version_id,
            name, kind, start_ts, end_ts, duration_ms, status,
            model_provider, model_name, model_params,
            tokens_in, tokens_out, input_excerpt, output_excerpt,
            content_hash_in, content_hash_out, signature_verified,
            tool_call_id, tool_name, tool_args_excerpt, tool_return_excerpt,
            policy_enforced, obligations, redaction_mask_ids, budget_enforced_cents, policy_allow,
            protocol, remote_agent_id, remote_version_id, request_id, edge_id,
            cost_cents, error_type, error_message, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
            $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
            $31, $32, $33, $34, $35, $36, $37, $38, $39, $40
        )
        ON CONFLICT (span_id) DO UPDATE SET
            end_ts = EXCLUDED.end_ts,
            duration_ms = EXCLUDED.duration_ms,
            status = EXCLUDED.status,
            output_excerpt = EXCLUDED.output_excerpt,
            content_hash_out = EXCLUDED.content_hash_out,
            cost_cents = EXCLUDED.cost_cents,
            error_type = EXCLUDED.error_type,
            error_message = EXCLUDED.error_message
        """,
        span_uuid, trace_uuid, parent_span_uuid, invocation_uuid, agent_uuid, version_uuid,
        name, kind, start_ts, end_ts, duration_ms, status,
        model_provider, model_name, json.dumps(model_params) if model_params else None,
        tokens_in, tokens_out, input_excerpt, output_excerpt,
        content_hash_in, content_hash_out, signature_verified,
        tool_call_id, tool_name, tool_args_excerpt, tool_return_excerpt,
        policy_enforced, obligations, redaction_mask_ids, budget_enforced_cents, policy_allow,
        protocol, remote_agent_uuid, remote_version_uuid, request_id, edge_uuid,
        cost_cents, error_type, error_message, json.dumps(metadata)
    )

    return span_uuid


async def _ingest_single_edge(edge_data: Dict[str, Any], user_id: str) -> uuid.UUID:
    """Insert a single edge into telemetry_edges table"""
    edge_id = edge_data.get("edge_id", str(uuid.uuid4()))
    edge_uuid = uuid.UUID(edge_id) if "-" in edge_id else uuid.uuid4()

    trace_uuid = uuid.UUID(edge_data["trace_id"])
    from_agent_uuid = uuid.UUID(edge_data["from_agent_id"])
    to_agent_uuid = uuid.UUID(edge_data["to_agent_id"])
    from_span_uuid = uuid.UUID(edge_data["from_span_id"])
    to_span_uuid = uuid.UUID(edge_data["to_span_id"])

    from_version_id = edge_data.get("from_version_id")
    to_version_id = edge_data.get("to_version_id")
    from_version_uuid = uuid.UUID(from_version_id) if from_version_id else None
    to_version_uuid = uuid.UUID(to_version_id) if to_version_id else None

    channel = edge_data["channel"]
    instruction_type = edge_data["instruction_type"]
    timestamp = _parse_timestamp(edge_data.get("timestamp", datetime.utcnow().isoformat()))
    latency_ms = edge_data.get("latency_ms")
    size_bytes = edge_data.get("size_bytes")
    content_hash = edge_data.get("content_hash")
    redaction_applied = edge_data.get("redaction_applied", False)
    signature_verified = edge_data.get("signature_verified", False)
    policy_enforced = edge_data.get("policy_enforced", [])
    obligations = edge_data.get("obligations", [])
    metadata = edge_data.get("metadata", {})

    await db.execute(
        """
        INSERT INTO telemetry_edges (
            edge_id, trace_id, from_agent_id, from_version_id, from_span_id,
            to_agent_id, to_version_id, to_span_id, channel, instruction_type,
            timestamp, latency_ms, size_bytes, content_hash,
            redaction_applied, signature_verified,
            policy_enforced, obligations, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19
        )
        ON CONFLICT (edge_id) DO UPDATE SET
            latency_ms = EXCLUDED.latency_ms,
            signature_verified = EXCLUDED.signature_verified
        """,
        edge_uuid, trace_uuid, from_agent_uuid, from_version_uuid, from_span_uuid,
        to_agent_uuid, to_version_uuid, to_span_uuid, channel, instruction_type,
        timestamp, latency_ms, size_bytes, content_hash,
        redaction_applied, signature_verified,
        policy_enforced, obligations, json.dumps(metadata)
    )

    return edge_uuid


async def _create_span_links(span_uuid: uuid.UUID, links: List[Dict[str, Any]]):
    """Create span links for OTel causality"""
    for link in links:
        linked_span_id = link.get("span_id")
        if not linked_span_id:
            continue

        linked_span_uuid = uuid.UUID(linked_span_id)
        link_type = link.get("type", "follows_from")
        attributes = link.get("attributes", {})

        await db.execute(
            """
            INSERT INTO span_links (span_id, linked_span_id, link_type, attributes)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (span_id, linked_span_id, link_type) DO NOTHING
            """,
            span_uuid, linked_span_uuid, link_type, json.dumps(attributes)
        )


async def _store_trace_context(trace_uuid: uuid.UUID, trace_context: Dict[str, Any]):
    """Store W3C trace context"""
    traceparent = trace_context.get("traceparent", "")
    tracestate = trace_context.get("tracestate", "")
    baggage = trace_context.get("baggage", {})
    run_mode = trace_context.get("run_mode", "normal")
    config_hash = trace_context.get("config_hash")

    await db.execute(
        """
        INSERT INTO trace_context (trace_id, traceparent, tracestate, baggage, run_mode, config_hash)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (trace_id) DO UPDATE SET
            traceparent = EXCLUDED.traceparent,
            tracestate = EXCLUDED.tracestate,
            baggage = EXCLUDED.baggage,
            run_mode = EXCLUDED.run_mode,
            config_hash = EXCLUDED.config_hash,
            updated_at = NOW()
        """,
        trace_uuid, traceparent, tracestate, json.dumps(baggage), run_mode, config_hash
    )


async def _run_detector(detector_name: str, span: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Run anomaly detector on span"""
    # Placeholder: implement actual detectors
    # This would call specialized detection functions

    if detector_name == "cost_outlier":
        # Use DB function
        agent_id = span["agent_id"]
        span_id = span["span_id"]
        cost = span.get("cost_cents", 0)

        if cost > 0:
            outliers = await db.fetch(
                "SELECT * FROM detect_cost_outliers($1, $2)",
                agent_id, 3.0
            )

            for outlier in outliers:
                if outlier["span_id"] == span_id:
                    # Found outlier
                    anomaly_id = await db.fetchval(
                        """
                        INSERT INTO span_anomalies (
                            span_id, trace_id, agent_id, anomaly_type, severity,
                            confidence, detector_name, evidence, status
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                        """,
                        span_id, span["trace_id"], agent_id, "cost_outlier", "medium",
                        0.95, "statistical_outlier", json.dumps(dict(outlier)), "open"
                    )

                    return {
                        "anomaly_id": str(anomaly_id),
                        "span_id": str(span_id),
                        "type": "cost_outlier",
                        "severity": "medium",
                        "confidence": 0.95
                    }

    # Add more detectors: prompt_injection, tool_abuse, context_tampering

    return None


def _parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp"""
    if not ts_str:
        return datetime.utcnow()

    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except ValueError:
        return datetime.utcnow()


def _serialize_span(span: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize span for JSON response"""
    for key in ["span_id", "trace_id", "parent_span_id", "invocation_id", "agent_id", "version_id",
                "remote_agent_id", "remote_version_id", "edge_id"]:
        if span.get(key):
            span[key] = str(span[key])

    for key in ["start_ts", "end_ts", "created_at"]:
        if span.get(key):
            span[key] = span[key].isoformat()

    return span


def _serialize_edge(edge: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize edge for JSON response"""
    for key in ["edge_id", "trace_id", "from_agent_id", "from_version_id", "from_span_id",
                "to_agent_id", "to_version_id", "to_span_id"]:
        if edge.get(key):
            edge[key] = str(edge[key])

    if edge.get("timestamp"):
        edge["timestamp"] = edge["timestamp"].isoformat()

    return edge
