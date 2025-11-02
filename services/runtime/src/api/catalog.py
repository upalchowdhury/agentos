"""
Exchange-Style Catalog API
US-R1: Browse/search agents/tools/prompts with badges
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


class Badge(str):
    """Quality badges for catalog items"""
    VERIFIED_TELEMETRY = "verified_telemetry"
    PARTIAL_TELEMETRY = "partial_telemetry"
    POLICY_CLEAN = "policy_clean"
    COST_TAGGED = "cost_tagged"
    HIGH_PERFORMANCE = "high_performance"
    PRODUCTION_READY = "production_ready"


class CatalogAgent(BaseModel):
    """Agent in catalog"""
    agent_id: str
    name: str
    description: Optional[str]
    owner_id: str
    model_type: str
    runtime: Optional[str]
    protocol: Optional[str]
    status: str
    badges: List[str]
    health_status: Optional[str]
    total_invocations: int
    success_rate_pct: float
    avg_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    total_cost_usd: float
    last_invoked_at: Optional[str]
    created_at: str
    deployed_at: Optional[str]


class CatalogFilters(BaseModel):
    """Filter options for catalog"""
    runtime: Optional[str] = None
    protocol: Optional[str] = None
    model_type: Optional[str] = None
    badges: List[str] = []
    status: Optional[str] = None
    health_status: Optional[str] = None
    min_success_rate: Optional[float] = None
    max_latency_ms: Optional[float] = None


async def calculate_badges(agent_row: dict) -> List[str]:
    """Calculate quality badges for an agent"""
    badges = []
    
    metadata = json.loads(agent_row.get("metadata", "{}"))
    
    # Verified Telemetry badge
    telemetry_quality = metadata.get("telemetry_quality", "")
    if telemetry_quality == "verified":
        badges.append(Badge.VERIFIED_TELEMETRY)
    elif telemetry_quality == "partial":
        badges.append(Badge.PARTIAL_TELEMETRY)
    
    # Policy Clean badge (no violations in last 30 days)
    has_violations = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM invocations
            WHERE agent_id = $1
            AND metadata->>'policy_violations' IS NOT NULL
            AND started_at > $2
        )
        """,
        agent_row["id"],
        datetime.utcnow() - timedelta(days=30),
    )
    
    if not has_violations:
        badges.append(Badge.POLICY_CLEAN)
    
    # Cost Tagged badge
    has_cost_tracking = await db.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM invocations
            WHERE agent_id = $1
            AND cost_decimal IS NOT NULL
            AND cost_decimal > 0
        )
        """,
        agent_row["id"],
    )
    
    if has_cost_tracking:
        badges.append(Badge.COST_TAGGED)
    
    # High Performance badge (p95 < 2000ms and success rate > 95%)
    if agent_row.get("p95_latency_ms") and agent_row["p95_latency_ms"] < 2000:
        success_rate = 0
        if agent_row.get("total_invocations") and agent_row["total_invocations"] > 0:
            success_rate = (agent_row.get("successful_invocations", 0) / agent_row["total_invocations"]) * 100
        
        if success_rate > 95:
            badges.append(Badge.HIGH_PERFORMANCE)
    
    # Production Ready badge
    if (
        agent_row.get("status") == "DEPLOYED" and
        agent_row.get("total_invocations", 0) > 100 and
        agent_row.get("health_status") == "healthy"
    ):
        badges.append(Badge.PRODUCTION_READY)
    
    return badges


@router.get("/agents", response_model=List[CatalogAgent])
async def browse_catalog(
    runtime: Optional[str] = None,
    protocol: Optional[str] = None,
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    badges: Optional[str] = Query(None, description="Comma-separated badges"),
    min_success_rate: Optional[float] = None,
    max_latency_ms: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="popularity", regex="^(popularity|cost|latency|created)$"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Browse catalog with filtering and search
    
    US-R1: Exchange-style catalog with filters and badges
    """
    # Build query
    conditions = []
    params = []
    param_idx = 1
    
    if runtime:
        conditions.append(f"a.runtime = ${param_idx}")
        params.append(runtime)
        param_idx += 1
    
    if model_type:
        conditions.append(f"a.model_type = ${param_idx}")
        params.append(model_type)
        param_idx += 1
    
    if status:
        conditions.append(f"a.status = ${param_idx}")
        params.append(status.upper())
        param_idx += 1
    
    if search:
        conditions.append(f"(a.name ILIKE ${param_idx} OR a.metadata->>'description' ILIKE ${param_idx})")
        params.append(f"%{search}%")
        param_idx += 1
    
    # Join with stats
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    # Determine sort order
    sort_clause = {
        "popularity": "stats.total_invocations DESC NULLS LAST",
        "cost": "stats.total_cost_usd DESC NULLS LAST",
        "latency": "stats.p95_latency_ms ASC NULLS LAST",
        "created": "a.created_at DESC",
    }[sort_by]
    
    query = f"""
    SELECT 
        a.*,
        stats.total_invocations,
        stats.successful_invocations,
        stats.failed_invocations,
        stats.p95_latency_ms,
        stats.avg_execution_time_ms,
        stats.total_cost_usd,
        stats.last_invoked_at
    FROM agents a
    LEFT JOIN agent_stats_v2 stats ON a.id = stats.agent_id
    WHERE {where_clause}
    ORDER BY {sort_clause}
    LIMIT {limit} OFFSET {offset}
    """
    
    rows = await db.fetch(query, *params)
    
    # Build catalog entries
    catalog_items = []
    for row in rows:
        # Calculate success rate
        success_rate = 0.0
        if row["total_invocations"] and row["total_invocations"] > 0:
            success_rate = (row["successful_invocations"] / row["total_invocations"]) * 100
        
        # Apply post-query filters
        if min_success_rate is not None and success_rate < min_success_rate:
            continue
        
        if max_latency_ms is not None:
            if not row["p95_latency_ms"] or row["p95_latency_ms"] > max_latency_ms:
                continue
        
        # Calculate badges
        agent_badges = await calculate_badges(row)
        
        # Filter by badges if specified
        if badges:
            requested_badges = [b.strip() for b in badges.split(",")]
            if not any(badge in agent_badges for badge in requested_badges):
                continue
        
        metadata = json.loads(row.get("metadata", "{}"))
        
        catalog_items.append(CatalogAgent(
            agent_id=str(row["id"]),
            name=row["name"],
            description=metadata.get("description"),
            owner_id=row["owner_id"],
            model_type=row["model_type"],
            runtime=row.get("runtime"),
            protocol=metadata.get("protocol"),
            status=row["status"],
            badges=agent_badges,
            health_status=row.get("health_status"),
            total_invocations=row["total_invocations"] or 0,
            success_rate_pct=round(success_rate, 2),
            avg_latency_ms=float(row["avg_execution_time_ms"]) if row["avg_execution_time_ms"] else None,
            p95_latency_ms=float(row["p95_latency_ms"]) if row["p95_latency_ms"] else None,
            total_cost_usd=float(row["total_cost_usd"]) if row["total_cost_usd"] else 0.0,
            last_invoked_at=row["last_invoked_at"].isoformat() if row["last_invoked_at"] else None,
            created_at=row["created_at"].isoformat(),
            deployed_at=row["deployed_at"].isoformat() if row["deployed_at"] else None,
        ))
    
    return catalog_items


@router.get("/agents/{agent_id}", response_model=CatalogAgent)
async def get_catalog_agent(agent_id: str):
    """Get detailed catalog entry for an agent"""
    try:
        agent_uuid = UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")
    
    row = await db.fetchrow(
        """
        SELECT 
            a.*,
            stats.total_invocations,
            stats.successful_invocations,
            stats.failed_invocations,
            stats.p95_latency_ms,
            stats.avg_execution_time_ms,
            stats.total_cost_usd,
            stats.last_invoked_at
        FROM agents a
        LEFT JOIN agent_stats_v2 stats ON a.id = stats.agent_id
        WHERE a.id = $1
        """,
        agent_uuid,
    )
    
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Calculate success rate
    success_rate = 0.0
    if row["total_invocations"] and row["total_invocations"] > 0:
        success_rate = (row["successful_invocations"] / row["total_invocations"]) * 100
    
    # Calculate badges
    agent_badges = await calculate_badges(row)
    
    metadata = json.loads(row.get("metadata", "{}"))
    
    return CatalogAgent(
        agent_id=str(row["id"]),
        name=row["name"],
        description=metadata.get("description"),
        owner_id=row["owner_id"],
        model_type=row["model_type"],
        runtime=row.get("runtime"),
        protocol=metadata.get("protocol"),
        status=row["status"],
        badges=agent_badges,
        health_status=row.get("health_status"),
        total_invocations=row["total_invocations"] or 0,
        success_rate_pct=round(success_rate, 2),
        avg_latency_ms=float(row["avg_execution_time_ms"]) if row["avg_execution_time_ms"] else None,
        p95_latency_ms=float(row["p95_latency_ms"]) if row["p95_latency_ms"] else None,
        total_cost_usd=float(row["total_cost_usd"]) if row["total_cost_usd"] else 0.0,
        last_invoked_at=row["last_invoked_at"].isoformat() if row["last_invoked_at"] else None,
        created_at=row["created_at"].isoformat(),
        deployed_at=row["deployed_at"].isoformat() if row["deployed_at"] else None,
    )


@router.get("/filters")
async def get_filter_options():
    """Get available filter options for catalog"""
    # Get unique values for each filter dimension
    runtimes = await db.fetch("SELECT DISTINCT runtime FROM agents WHERE runtime IS NOT NULL ORDER BY runtime")
    protocols = await db.fetch(
        "SELECT DISTINCT metadata->>'protocol' as protocol FROM agents WHERE metadata->>'protocol' IS NOT NULL"
    )
    
    return {
        "runtimes": [r["runtime"] for r in runtimes],
        "protocols": [p["protocol"] for p in protocols if p["protocol"]],
        "model_types": ["A", "B"],
        "statuses": ["PENDING", "BUILDING", "DEPLOYED", "FAILED", "STOPPED"],
        "health_statuses": ["healthy", "unhealthy", "unknown"],
        "badges": [
            Badge.VERIFIED_TELEMETRY,
            Badge.PARTIAL_TELEMETRY,
            Badge.POLICY_CLEAN,
            Badge.COST_TAGGED,
            Badge.HIGH_PERFORMANCE,
            Badge.PRODUCTION_READY,
        ],
        "sort_options": ["popularity", "cost", "latency", "created"],
    }


@router.get("/stats")
async def get_catalog_stats():
    """Get overall catalog statistics"""
    stats = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as total_agents,
            COUNT(*) FILTER (WHERE model_type = 'A') as model_a_count,
            COUNT(*) FILTER (WHERE model_type = 'B') as model_b_count,
            COUNT(*) FILTER (WHERE status = 'DEPLOYED') as deployed_count,
            COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy_count
        FROM agents
        """
    )
    
    invocations_stats = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as total_invocations,
            COUNT(DISTINCT agent_id) as agents_with_invocations,
            COALESCE(SUM(cost_decimal), 0.0) as total_cost
        FROM invocations
        WHERE started_at > $1
        """,
        datetime.utcnow() - timedelta(days=30),
    )
    
    return {
        "total_agents": stats["total_agents"],
        "model_a_agents": stats["model_a_count"],
        "model_b_agents": stats["model_b_count"],
        "deployed_agents": stats["deployed_count"],
        "healthy_agents": stats["healthy_count"],
        "total_invocations_30d": invocations_stats["total_invocations"],
        "active_agents_30d": invocations_stats["agents_with_invocations"],
        "total_cost_30d_usd": float(invocations_stats["total_cost"]),
    }
