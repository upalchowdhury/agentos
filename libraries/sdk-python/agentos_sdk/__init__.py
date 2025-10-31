"""
AgentOS Python SDK for Model B Agents

Enables external agents to emit Agent Telemetry Protocol (ATP) v0 traces
and integrate with AgentOS observability platform.
"""

from .client import AgentOSClient
from .telemetry import TelemetryBuilder, StepBuilder
from .models import StepKind, InvocationStatus

__version__ = "0.1.0"
__all__ = [
    "AgentOSClient",
    "TelemetryBuilder",
    "StepBuilder",
    "StepKind",
    "InvocationStatus",
]
