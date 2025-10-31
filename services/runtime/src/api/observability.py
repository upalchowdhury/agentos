import csv
import io
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..database import db
from ..models_v2 import ObservabilityAgentSummary, ObservabilityTrace, ObservabilityTraceStep
from .agents_v2 import get_current_user, _load_metadata


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/observability", tags=["observability"])


def _parse_iso_datetime(value: Optional[str], field: str) -> datetime:
    if not value:
        raise HTTPException(status_code=400, detail=f"Missing required '{field}' parameter")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError as exc:  # pragma: no cover - FastAPI handles
        raise HTTPException(status_code=400, detail=f"Invalid datetime for '{field}'") from exc
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _serialize_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.replace(microsecond=0).isoformat() + "Z"


@router.get("/agents", response_model=List[ObservabilityAgentSummary])
async def get_observability_agents(
    range: str = "1d",
    user_id: str = Depends(get_current_user),
):
    range_map = {"1h": 1, "6h": 6, "12h": 12, "1d": 24, "7d": 168, "30d": 720}
    hours = range_map.get(range, 24)

    now = datetime.utcnow()
    window_start = now - timedelta(hours=hours)

    agents = await db.fetch(
        """
        SELECT id, name, metadata, model_type, runtime
        FROM agents
        WHERE owner_id = $1
        """,
        user_id,
    )

    if not agents:
        return []

    agent_map: Dict[str, Dict] = {}
    for row in agents:
        metadata = _load_metadata(row)
        telemetry_quality = metadata.get("telemetry_quality")
        if not telemetry_quality:
            telemetry_quality = "verified" if row.get("model_type") == "A" else "partial"

        agent_map[str(row["id"])] = {
            "name": row["name"],
            "metadata": metadata,
            "telemetry_quality": telemetry_quality,
        }

    invocation_rows = await db.fetch(
        """
        SELECT agent_id, status, execution_time_ms, cost_decimal, metadata
        FROM invocations
        WHERE started_at >= $1
        """,
        window_start,
    )

    aggregates: Dict[str, Dict[str, List]] = defaultdict(lambda: {
        "latencies": [],
        "cost": 0.0,
        "success": 0,
        "total": 0,
        "error": 0,
        "denied": 0,
        "policy_alerts": 0,
    })

    for row in invocation_rows:
        agent_id = str(row["agent_id"])
        if agent_id not in agent_map:
            continue
        agg = aggregates[agent_id]
        agg["total"] += 1
        status = row["status"]
        if status == "SUCCESS":
            agg["success"] += 1
        else:
            agg["error"] += 1
        if status == "DENIED":
            agg["denied"] += 1
        latency = row.get("execution_time_ms")
        if latency is not None:
            agg["latencies"].append(int(latency))
        cost = row.get("cost_decimal")
        if cost is not None:
            agg["cost"] += float(cost)

        metadata = row.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        if isinstance(metadata, dict):
            policy_alerts = metadata.get("policy_alerts")
            if isinstance(policy_alerts, dict):
                agg["policy_alerts"] += len(policy_alerts)

    summaries: List[ObservabilityAgentSummary] = []
    for agent_id, info in agent_map.items():
        agg = aggregates.get(agent_id, {"total": 0, "success": 0, "error": 0, "latencies": [], "cost": 0.0, "denied": 0, "policy_alerts": 0})
        total = agg["total"]
        success = agg.get("success", 0)
        error = agg.get("error", 0)

        success_rate = (success / total) if total else 0.0
        error_rate = (error / total) if total else 0.0

        latencies = sorted(agg.get("latencies", []))
        if latencies:
            index = max(0, int(len(latencies) * 0.95) - 1)
            p95 = float(latencies[index])
        else:
            p95 = None

        summaries.append(
            ObservabilityAgentSummary(
                agent_id=agent_id,
                name=info["name"],
                telemetry_quality=info["telemetry_quality"],
                total_invocations=total,
                success_rate=success_rate,
                error_rate=error_rate,
                p95_latency_ms=p95,
                cost_usd=agg.get("cost", 0.0),
                denied_invocations=agg.get("denied", 0),
                policy_alerts_count=agg.get("policy_alerts", 0),
                time_range_start=window_start,
                time_range_end=now,
            )
        )

    summaries.sort(key=lambda item: item.total_invocations, reverse=True)
    return summaries


@router.get("/agents/invocations")
async def get_recent_invocations(
    limit: int = 20,
    query: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    limit = max(1, min(limit, 200))

    filter_pattern = f"%{query.lower()}%" if query else None

    base_query = """
        SELECT i.id, i.agent_id, i.status, i.started_at, i.execution_time_ms, i.metadata,
               i.requester_id, i.caller_agent_id,
               a.name, a.metadata AS agent_metadata
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE a.owner_id = $1
    """

    params = [user_id]
    if filter_pattern:
        base_query += " AND (LOWER(a.name) LIKE $2 OR CAST(i.id AS TEXT) LIKE $2 OR CAST(i.agent_id AS TEXT) LIKE $2)"
        params.append(filter_pattern)

    base_query += " ORDER BY i.started_at DESC LIMIT $%d" % (len(params) + 1)
    params.append(limit)

    rows = await db.fetch(base_query, *params)

    def extract_trace_id(metadata: Dict[str, Any]) -> Optional[str]:
        trace = metadata.get("trace") if isinstance(metadata, dict) else None
        if isinstance(trace, dict):
            return trace.get("trace_id")
        return None

    invocations = []
    for row in rows:
        invocation_metadata = row.get("metadata") or {}
        if isinstance(invocation_metadata, str):
            try:
                invocation_metadata = json.loads(invocation_metadata)
            except json.JSONDecodeError:  # pragma: no cover
                invocation_metadata = {}

        agent_metadata = _load_metadata(row)
        telemetry_quality = invocation_metadata.get("telemetry_quality") or agent_metadata.get("telemetry_quality")

        actor = invocation_metadata.get("actor") if isinstance(invocation_metadata, dict) else {}
        requester_id = actor.get("requester_id") or row.get("requester_id")
        caller_agent_id_raw = actor.get("caller_agent_id") or row.get("caller_agent_id")
        caller_agent_id = str(caller_agent_id_raw) if caller_agent_id_raw else None
        subject_type = actor.get("subject_type") or ("agent" if caller_agent_id else "user")
        invocations.append(
            {
                "invocation_id": str(row["id"]),
                "agent_id": str(row["agent_id"]),
                "agent_name": row["name"],
                "status": row["status"],
                "started_at": row["started_at"],
                "execution_time_ms": row.get("execution_time_ms"),
                "telemetry_quality": telemetry_quality or "partial",
                "trace_id": extract_trace_id(invocation_metadata),
                "requester_id": requester_id,
                "caller_agent_id": caller_agent_id,
                "subject_type": subject_type,
                "actor": {
                    "requester_id": requester_id,
                    "caller_agent_id": caller_agent_id,
                    "subject_type": subject_type,
                },
            }
        )

    return invocations


@router.get("/agents/trace/{invocation_id}", response_model=ObservabilityTrace)
async def get_trace_details(
    invocation_id: str,
    user_id: str = Depends(get_current_user),
):
    record = await db.fetchrow(
        """
        SELECT i.*, a.name AS agent_name, a.metadata AS agent_metadata
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE i.id = $1 AND a.owner_id = $2
        """,
        uuid.UUID(invocation_id),
        user_id,
    )

    if not record:
        raise HTTPException(status_code=404, detail="Invocation not found")

    metadata = record.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    trace = metadata.get("trace") or {}
    if not isinstance(trace, dict):
        trace = {}

    trace_id = trace.get("trace_id") or uuid.uuid4().hex
    steps = trace.get("steps") or []
    normalized_steps: List[ObservabilityTraceStep] = []
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        normalized_steps.append(
            ObservabilityTraceStep(
                step_id=step.get("step_id") or f"{trace_id}-step-{idx}",
                parent_step_id=step.get("parent_step_id"),
                name=step.get("name", "step"),
                kind=step.get("kind", "system"),
                status=step.get("status", record["status"]),
                start_ts=step.get("start_ts"),
                end_ts=step.get("end_ts"),
                latency_ms=step.get("latency_ms"),
                error_type=step.get("error_type"),
                error_message=step.get("error_message"),
                input_excerpt=step.get("input_excerpt"),
                output_excerpt=step.get("output_excerpt"),
            )
        )

    actor_context = metadata.get("actor")
    if not isinstance(actor_context, dict):
        actor_context = {
            "requester_id": record.get("requester_id"),
            "caller_agent_id": record.get("caller_agent_id"),
            "subject_type": "agent" if record.get("caller_agent_id") else "user",
            "subject_id": record.get("caller_agent_id") or record.get("requester_id"),
        }

    policy_data = metadata.get("policy") if isinstance(metadata, dict) else None
    if not isinstance(policy_data, dict):
        policy_data = None

    policy_alerts = metadata.get("policy_alerts") if isinstance(metadata, dict) else None
    if not isinstance(policy_alerts, dict):
        policy_alerts = None

    logs = metadata.get("logs")
    if not isinstance(logs, list):
        logs = trace.get("logs")
    normalized_logs: List[Dict[str, Any]] = []
    if isinstance(logs, list):
        for log in logs:
            if not isinstance(log, dict):
                continue
            enriched_log = dict(log)
            enriched_log.setdefault("actor", actor_context)
            if "requester_id" not in enriched_log:
                enriched_log["requester_id"] = actor_context.get("requester_id")
            if "caller_agent_id" not in enriched_log:
                enriched_log["caller_agent_id"] = actor_context.get("caller_agent_id")
            if policy_alerts and "policy_alerts" not in enriched_log:
                enriched_log["policy_alerts"] = policy_alerts
            normalized_logs.append(enriched_log)

    telemetry_quality = metadata.get("telemetry_quality")
    if not telemetry_quality:
        agent_metadata = _load_metadata(record)
        telemetry_quality = agent_metadata.get("telemetry_quality", "partial")

    return ObservabilityTrace(
        trace_id=trace_id,
        invocation_id=invocation_id,
        agent_id=str(record["agent_id"]),
        agent_name=record["agent_name"],
        telemetry_quality=telemetry_quality,
        status=record["status"],
        start_ts=trace.get("start_ts") or record.get("started_at"),
        end_ts=trace.get("end_ts") or record.get("ended_at"),
        execution_time_ms=trace.get("execution_time_ms") or record.get("execution_time_ms"),
        cost_usd=float(record.get("cost_decimal") or 0.0),
        requester_id=actor_context.get("requester_id"),
        caller_agent_id=str(actor_context.get("caller_agent_id")) if actor_context.get("caller_agent_id") else None,
        actor=actor_context,
        policy=policy_data,
        policy_alerts=policy_alerts,
        steps=normalized_steps,
        logs=normalized_logs,
    )


def _build_audit_row(record: Dict[str, Any]) -> Dict[str, Any]:
    metadata = record.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    actor = metadata.get("actor") if isinstance(metadata, dict) else {}
    if not isinstance(actor, dict):
        actor = {}

    subject_type = actor.get("subject_type") or ("agent" if actor.get("caller_agent_id") else "user")
    policy_alerts = metadata.get("policy_alerts") if isinstance(metadata, dict) else None
    policy_alert_count = len(policy_alerts) if isinstance(policy_alerts, dict) else 0

    policy = metadata.get("policy") if isinstance(metadata, dict) else None
    obligations = {}
    if isinstance(policy, dict):
        obligations = policy.get("obligations", {}) or {}

    return {
        "invocation_id": str(record["id"]),
        "agent_id": str(record["agent_id"]),
        "agent_name": record.get("agent_name") or "",
        "status": record.get("status", ""),
        "requester_id": actor.get("requester_id") or record.get("requester_id"),
        "caller_agent_id": actor.get("caller_agent_id") or record.get("caller_agent_id"),
        "subject_type": subject_type,
        "started_at": _serialize_datetime(record.get("started_at")),
        "ended_at": _serialize_datetime(record.get("ended_at")),
        "execution_time_ms": record.get("execution_time_ms") or 0,
        "cost_usd": float(record.get("cost_decimal") or 0.0),
        "policy_alerts": policy_alert_count,
        "policy_obligations": json.dumps(obligations) if obligations else "",
    }


def _stream_csv(rows: Iterable[Dict[str, Any]], headers: List[str]) -> Iterable[str]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in rows:
        writer.writerow([row.get(column, "") for column in headers])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


@router.get("/audit/export")
async def export_audit_logs(
    start: Optional[str] = None,
    end: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 2000,
    user_id: str = Depends(get_current_user),
):
    now = datetime.utcnow()
    end_dt = _parse_iso_datetime(end, "end") if end else now
    start_dt = _parse_iso_datetime(start, "start") if start else end_dt - timedelta(days=7)

    if start_dt > end_dt:
        raise HTTPException(status_code=400, detail="'start' must be earlier than 'end'")

    limit = max(1, min(limit, 10000))

    conditions = ["a.owner_id = $1", "i.started_at >= $2", "i.started_at <= $3"]
    params: List[Any] = [user_id, start_dt, end_dt]

    param_index = 4
    if agent_id:
        try:
            agent_uuid = uuid.UUID(agent_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid agent_id") from exc
        conditions.append(f"i.agent_id = ${param_index}")
        params.append(agent_uuid)
        param_index += 1

    if status:
        conditions.append(f"i.status = ${param_index}")
        params.append(status.upper())
        param_index += 1

    query = f"""
        SELECT i.id, i.agent_id, a.name AS agent_name, i.requester_id, i.caller_agent_id,
               i.status, i.started_at, i.ended_at, i.execution_time_ms, i.cost_decimal, i.metadata
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE {' AND '.join(conditions)}
        ORDER BY i.started_at DESC
        LIMIT ${param_index}
    """

    params.append(limit)

    rows = await db.fetch(query, *params)

    audit_rows = [_build_audit_row(dict(row)) for row in rows]
    headers = [
        "invocation_id",
        "agent_id",
        "agent_name",
        "status",
        "requester_id",
        "caller_agent_id",
        "subject_type",
        "started_at",
        "ended_at",
        "execution_time_ms",
        "cost_usd",
        "policy_alerts",
        "policy_obligations",
    ]

    stream = _stream_csv(audit_rows, headers)
    filename = f"audit_export_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        (chunk.encode("utf-8") for chunk in stream),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/logs")
async def get_logs(
    limit: int = 200,
    trace_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    level: Optional[str] = None,
    subject_type: Optional[str] = None,
    requester_id: Optional[str] = None,
    caller_agent_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    limit = max(1, min(limit, 500))

    rows = await db.fetch(
        """
        SELECT i.metadata, i.id, i.agent_id, i.started_at, i.requester_id, i.caller_agent_id, a.name
        FROM invocations i
        JOIN agents a ON i.agent_id = a.id
        WHERE a.owner_id = $1
        ORDER BY i.started_at DESC
        """,
        user_id,
    )

    entries: List[Dict[str, Any]] = []
    trace_id_lower = trace_id.lower() if trace_id else None
    agent_id_lower = agent_id.lower() if agent_id else None
    level_lower = level.lower() if level else None
    subject_type_lower = subject_type.lower() if subject_type else None
    requester_lower = requester_id.lower() if requester_id else None
    caller_lower = caller_agent_id.lower() if caller_agent_id else None

    for row in rows:
        metadata = row.get("metadata") or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}

        trace = metadata.get("trace") if isinstance(metadata, dict) else None
        row_trace_id = trace.get("trace_id") if isinstance(trace, dict) else None

        if trace_id_lower and (not row_trace_id or trace_id_lower not in row_trace_id.lower()):
            continue
        if agent_id_lower and agent_id_lower not in str(row["agent_id"]).lower():
            continue

        actor_context = metadata.get("actor") if isinstance(metadata, dict) else None
        if not isinstance(actor_context, dict):
            actor_context = {
                "requester_id": row.get("requester_id"),
                "caller_agent_id": row.get("caller_agent_id"),
                "subject_type": "agent" if row.get("caller_agent_id") else "user",
                "subject_id": row.get("caller_agent_id") or row.get("requester_id"),
            }

        policy_alerts = metadata.get("policy_alerts") if isinstance(metadata, dict) else None
        if not isinstance(policy_alerts, dict):
            policy_alerts = None

        logs = metadata.get("logs") if isinstance(metadata, dict) else None
        if not isinstance(logs, list):
            continue

        for log in logs:
            if not isinstance(log, dict):
                continue
            log_actor = log.get("actor") if isinstance(log, dict) else None
            if not isinstance(log_actor, dict):
                log_actor = actor_context
            log_level = str(log.get("level") or "").lower()
            if level_lower and log_level != level_lower:
                continue
            actor_subject_type = str(log_actor.get("subject_type") or "").lower()
            if subject_type_lower and actor_subject_type != subject_type_lower:
                continue
            raw_requester = log_actor.get("requester_id")
            actor_requester_lower = str(raw_requester).lower() if raw_requester else ""
            if requester_lower and requester_lower not in actor_requester_lower:
                continue
            actor_caller = log_actor.get("caller_agent_id")
            actor_caller_lower = str(actor_caller).lower() if actor_caller else ""
            if caller_lower and caller_lower not in actor_caller_lower:
                continue
            entry = {
                "timestamp": log.get("timestamp") or row["started_at"].isoformat(),
                "level": log.get("level", "INFO"),
                "message": log.get("message", ""),
                "trace_id": log.get("trace_id") or row_trace_id,
                "agent_id": str(row["agent_id"]),
                "agent_name": row["name"],
                "invocation_id": str(row["id"]),
                "requester_id": log_actor.get("requester_id"),
                "caller_agent_id": str(log_actor.get("caller_agent_id")) if log_actor.get("caller_agent_id") else None,
                "subject_type": log_actor.get("subject_type"),
                "actor": log_actor,
            }
            if policy_alerts and "policy_alerts" not in log:
                entry["policy_alerts"] = policy_alerts
            elif isinstance(log.get("policy_alerts"), dict):
                entry["policy_alerts"] = log.get("policy_alerts")
            entries.append(entry)

    entries.sort(key=lambda entry: entry["timestamp"], reverse=True)
    return entries[:limit]
