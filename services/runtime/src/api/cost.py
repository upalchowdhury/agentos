"""
Cost Tracking API Endpoints
US-A3: Cost attribution per invocation and MTD aggregates
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..cost_tracking import cost_tracker
from ..database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/cost", tags=["cost"])


class CostSummaryResponse(BaseModel):
    """Cost summary response"""
    period_days: int
    invocation_count: int
    successful_count: int
    failed_count: int
    total_cost_usd: float
    avg_cost_per_invocation_usd: float


class TopSpendingAgent(BaseModel):
    """Top spending agent"""
    agent_id: str
    agent_name: str
    owner_id: str
    invocation_count: int
    total_cost_usd: float
    avg_cost_usd: float


class BudgetStatus(BaseModel):
    """Budget check result"""
    agent_id: str
    agent_name: str
    within_budget: bool
    current_spend_usd: float
    budget_limit_usd: float
    period: str


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    agent_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    period_days: int = Query(default=30, le=365),
):
    """
    Get cost summary for agents
    
    US-A3: Cost attribution - MTD aggregates
    """
    agent_uuid = None
    if agent_id:
        try:
            agent_uuid = UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id format")
    
    summary = await cost_tracker.get_cost_summary(
        agent_id=agent_uuid,
        owner_id=owner_id,
        period_days=period_days,
    )
    
    return CostSummaryResponse(**summary)


@router.get("/top-spending", response_model=list[TopSpendingAgent])
async def get_top_spending_agents(
    owner_id: Optional[str] = None,
    limit: int = Query(default=10, le=100),
    period_days: int = Query(default=30, le=365),
):
    """
    Get top spending agents for FinOps analysis
    """
    agents = await cost_tracker.get_top_spending_agents(
        owner_id=owner_id,
        limit=limit,
        period_days=period_days,
    )
    
    return [TopSpendingAgent(**agent) for agent in agents]


@router.get("/agents/{agent_id}/budget", response_model=BudgetStatus)
async def check_agent_budget(
    agent_id: str,
    budget_limit_usd: float = Query(default=100.0),
    period: str = Query(default="daily", regex="^(daily|monthly)$"),
):
    """
    Check if agent is within budget
    
    US-A4: Budget caps enforcement
    """
    try:
        agent_uuid = UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")
    
    # Get agent info
    agent = await db.fetchrow(
        "SELECT id, name FROM agents WHERE id = $1",
        agent_uuid,
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    within_budget, current_spend, limit = await cost_tracker.check_budget(
        agent_id=agent_uuid,
        budget_limit=budget_limit_usd,
        period=period,
    )
    
    return BudgetStatus(
        agent_id=agent_id,
        agent_name=agent["name"],
        within_budget=within_budget,
        current_spend_usd=float(current_spend),
        budget_limit_usd=float(limit),
        period=period,
    )


@router.post("/aggregate")
async def trigger_cost_aggregation():
    """
    Manually trigger cost aggregation
    Normally runs via cron, but can be triggered for testing
    """
    try:
        await cost_tracker.aggregate_daily_costs()
        
        return {
            "status": "success",
            "message": "Cost aggregation completed",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Cost aggregation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cost aggregation failed: {str(e)}",
        )
