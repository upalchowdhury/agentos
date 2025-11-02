"""
Cost Tracking & Budget Enforcement
Tracks costs per invocation, enforces budget caps, provides FinOps reporting
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from .database import db

logger = logging.getLogger(__name__)


class CostAdapter:
    """Base adapter for provider-specific cost calculation"""
    
    def calculate_cost(self, usage: Dict) -> Decimal:
        """Calculate cost from usage metrics"""
        raise NotImplementedError


class OpenAICostAdapter(CostAdapter):
    """Cost adapter for OpenAI models"""
    
    PRICING = {
        "gpt-4": {"input": Decimal("0.00003"), "output": Decimal("0.00006")},
        "gpt-4-turbo": {"input": Decimal("0.00001"), "output": Decimal("0.00003")},
        "gpt-3.5-turbo": {"input": Decimal("0.0000005"), "output": Decimal("0.0000015")},
    }
    
    def calculate_cost(self, usage: Dict) -> Decimal:
        model = usage.get("model", "gpt-3.5-turbo")
        tokens_in = usage.get("tokens_in", 0)
        tokens_out = usage.get("tokens_out", 0)
        
        pricing = self.PRICING.get(model, self.PRICING["gpt-3.5-turbo"])
        
        cost = (tokens_in * pricing["input"]) + (tokens_out * pricing["output"])
        return cost


class AnthropicCostAdapter(CostAdapter):
    """Cost adapter for Anthropic models"""
    
    PRICING = {
        "claude-3-opus": {"input": Decimal("0.000015"), "output": Decimal("0.000075")},
        "claude-3-sonnet": {"input": Decimal("0.000003"), "output": Decimal("0.000015")},
        "claude-3-haiku": {"input": Decimal("0.00000025"), "output": Decimal("0.00000125")},
    }
    
    def calculate_cost(self, usage: Dict) -> Decimal:
        model = usage.get("model", "claude-3-sonnet")
        tokens_in = usage.get("tokens_in", 0)
        tokens_out = usage.get("tokens_out", 0)
        
        pricing = self.PRICING.get(model, self.PRICING["claude-3-sonnet"])
        
        cost = (tokens_in * pricing["input"]) + (tokens_out * pricing["output"])
        return cost


class GeminiCostAdapter(CostAdapter):
    """Cost adapter for Google Gemini models"""
    
    PRICING = {
        "gemini-pro": {"input": Decimal("0.0000005"), "output": Decimal("0.0000015")},
        "gemini-ultra": {"input": Decimal("0.000002"), "output": Decimal("0.000006")},
    }
    
    def calculate_cost(self, usage: Dict) -> Decimal:
        model = usage.get("model", "gemini-pro")
        tokens_in = usage.get("tokens_in", 0)
        tokens_out = usage.get("tokens_out", 0)
        
        pricing = self.PRICING.get(model, self.PRICING["gemini-pro"])
        
        cost = (tokens_in * pricing["input"]) + (tokens_out * pricing["output"])
        return cost


class BedrockCostAdapter(CostAdapter):
    """Cost adapter for AWS Bedrock models"""
    
    PRICING = {
        "anthropic.claude-v2": {"input": Decimal("0.00001"), "output": Decimal("0.00003")},
        "meta.llama2-70b": {"input": Decimal("0.00000195"), "output": Decimal("0.00000256")},
    }
    
    def calculate_cost(self, usage: Dict) -> Decimal:
        model = usage.get("model", "anthropic.claude-v2")
        tokens_in = usage.get("tokens_in", 0)
        tokens_out = usage.get("tokens_out", 0)
        
        pricing = self.PRICING.get(model, self.PRICING["anthropic.claude-v2"])
        
        cost = (tokens_in * pricing["input"]) + (tokens_out * pricing["output"])
        return cost


class ComputeCostAdapter(CostAdapter):
    """Cost adapter for compute resources"""
    
    PRICING = {
        "cpu_second": Decimal("0.00001"),
        "memory_mb_second": Decimal("0.000001"),
    }
    
    def calculate_cost(self, usage: Dict) -> Decimal:
        cpu_seconds = usage.get("cpu_seconds", 0)
        memory_mb_seconds = usage.get("memory_mb_seconds", 0)
        
        cost = (cpu_seconds * self.PRICING["cpu_second"]) + \
               (memory_mb_seconds * self.PRICING["memory_mb_second"])
        
        return cost


class CostTracker:
    """Main cost tracking and budget enforcement"""
    
    def __init__(self):
        self.adapters = {
            "openai": OpenAICostAdapter(),
            "anthropic": AnthropicCostAdapter(),
            "gemini": GeminiCostAdapter(),
            "bedrock": BedrockCostAdapter(),
            "compute": ComputeCostAdapter(),
        }
    
    def calculate_invocation_cost(
        self,
        provider: str,
        usage_data: Dict,
    ) -> Decimal:
        """
        Calculate cost for a single invocation
        
        Args:
            provider: Provider name (openai, anthropic, etc.)
            usage_data: Dict with tokens_in, tokens_out, model, etc.
        
        Returns:
            Cost in USD
        """
        adapter = self.adapters.get(provider.lower())
        
        if not adapter:
            logger.warning(f"Unknown provider: {provider}, using default pricing")
            # Fallback to basic token pricing
            tokens_in = usage_data.get("tokens_in", 0)
            tokens_out = usage_data.get("tokens_out", 0)
            return Decimal(tokens_in + tokens_out) * Decimal("0.000001")
        
        return adapter.calculate_cost(usage_data)
    
    async def record_invocation_cost(
        self,
        invocation_id: UUID,
        agent_id: UUID,
        cost_breakdown: Dict[str, Decimal],
    ):
        """
        Record cost for an invocation
        
        Args:
            invocation_id: Invocation UUID
            agent_id: Agent UUID
            cost_breakdown: Dict mapping cost categories to amounts
        """
        total_cost = sum(cost_breakdown.values())
        
        # Update invocation record
        await db.execute(
            """
            UPDATE invocations 
            SET cost_decimal = $1, cost_breakdown = $2
            WHERE id = $3
            """,
            total_cost,
            cost_breakdown,
            invocation_id,
        )
        
        logger.info(
            f"Recorded cost for invocation {invocation_id}: ${total_cost:.4f}"
        )
    
    async def check_budget(
        self,
        agent_id: UUID,
        budget_limit: Optional[Decimal] = None,
        period: str = "daily",
    ) -> tuple[bool, Decimal, Decimal]:
        """
        Check if agent is within budget
        
        Args:
            agent_id: Agent UUID
            budget_limit: Budget limit in USD (None = no limit)
            period: Budget period (daily, monthly)
        
        Returns:
            (within_budget, current_spend, limit)
        """
        if budget_limit is None:
            return True, Decimal(0), Decimal(0)
        
        # Calculate period start
        now = datetime.utcnow()
        if period == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            period_start = now - timedelta(days=1)
        
        # Get current spend
        row = await db.fetchrow(
            """
            SELECT COALESCE(SUM(cost_decimal), 0.0) as total_cost
            FROM invocations
            WHERE agent_id = $1 AND started_at >= $2
            """,
            agent_id,
            period_start,
        )
        
        current_spend = Decimal(row["total_cost"])
        within_budget = current_spend < budget_limit
        
        if not within_budget:
            logger.warning(
                f"Agent {agent_id} exceeded {period} budget: "
                f"${current_spend:.2f} / ${budget_limit:.2f}"
            )
        
        return within_budget, current_spend, budget_limit
    
    async def get_cost_summary(
        self,
        agent_id: Optional[UUID] = None,
        owner_id: Optional[str] = None,
        period_days: int = 30,
    ) -> Dict:
        """
        Get cost summary for an agent or owner
        
        Returns:
            Dict with total_cost, invocation_count, breakdown by provider
        """
        conditions = []
        params = []
        param_idx = 1
        
        if agent_id:
            conditions.append(f"agent_id = ${param_idx}")
            params.append(agent_id)
            param_idx += 1
        
        if owner_id:
            conditions.append(f"agent_id IN (SELECT id FROM agents WHERE owner_id = ${param_idx})")
            params.append(owner_id)
            param_idx += 1
        
        # Time filter
        start_date = datetime.utcnow() - timedelta(days=period_days)
        conditions.append(f"started_at >= ${param_idx}")
        params.append(start_date)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
        SELECT 
            COUNT(*) as invocation_count,
            COALESCE(SUM(cost_decimal), 0.0) as total_cost,
            COALESCE(AVG(cost_decimal), 0.0) as avg_cost_per_invocation,
            COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful_count,
            COUNT(*) FILTER (WHERE status != 'SUCCESS') as failed_count
        FROM invocations
        WHERE {where_clause}
        """
        
        row = await db.fetchrow(query, *params)
        
        return {
            "period_days": period_days,
            "invocation_count": row["invocation_count"],
            "successful_count": row["successful_count"],
            "failed_count": row["failed_count"],
            "total_cost_usd": float(row["total_cost"]),
            "avg_cost_per_invocation_usd": float(row["avg_cost_per_invocation"]),
        }
    
    async def aggregate_daily_costs(self, date: Optional[datetime] = None):
        """
        Aggregate costs into cost_snapshots for reporting
        Should be run daily via cron/scheduler
        """
        if date is None:
            date = datetime.utcnow().date() - timedelta(days=1)
        
        # Call database function
        await db.execute("SELECT aggregate_daily_costs($1)", date)
        
        logger.info(f"Aggregated costs for {date}")
    
    async def get_top_spending_agents(
        self,
        owner_id: Optional[str] = None,
        limit: int = 10,
        period_days: int = 30,
    ) -> List[Dict]:
        """Get top spending agents for cost analysis"""
        conditions = ["i.started_at >= $1"]
        params = [datetime.utcnow() - timedelta(days=period_days)]
        param_idx = 2
        
        if owner_id:
            conditions.append(f"a.owner_id = ${param_idx}")
            params.append(owner_id)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            a.id as agent_id,
            a.name as agent_name,
            a.owner_id,
            COUNT(i.id) as invocation_count,
            COALESCE(SUM(i.cost_decimal), 0.0) as total_cost,
            COALESCE(AVG(i.cost_decimal), 0.0) as avg_cost
        FROM agents a
        JOIN invocations i ON a.id = i.agent_id
        WHERE {where_clause}
        GROUP BY a.id, a.name, a.owner_id
        ORDER BY total_cost DESC
        LIMIT {limit}
        """
        
        rows = await db.fetch(query, *params)
        
        return [
            {
                "agent_id": str(row["agent_id"]),
                "agent_name": row["agent_name"],
                "owner_id": row["owner_id"],
                "invocation_count": row["invocation_count"],
                "total_cost_usd": float(row["total_cost"]),
                "avg_cost_usd": float(row["avg_cost"]),
            }
            for row in rows
        ]


# Global cost tracker instance
cost_tracker = CostTracker()
