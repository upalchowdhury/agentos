import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AgentMonitor:
    """
    Agent monitor for tracking resource usage and health.
    TODO: Implement metrics collection and alerting.
    """
    
    def __init__(self) -> None:
        self.metrics_enabled: bool = False
    
    async def collect_metrics(self, agent_id: str) -> dict[str, float]:
        """
        Collect current metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary of metrics (cpu_percent, memory_mb, etc.)
        """
        raise NotImplementedError("Metrics collection not yet implemented")
    
    async def record_metric(
        self,
        agent_id: str,
        metric_name: str,
        value: float
    ) -> None:
        """
        Record a metric value for an agent.
        
        Args:
            agent_id: Agent identifier
            metric_name: Name of the metric
            value: Metric value
        """
        raise NotImplementedError("Metric recording not yet implemented")
