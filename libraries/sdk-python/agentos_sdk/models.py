"""Data models for AgentOS SDK"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


class StepKind(str, Enum):
    """Type of step in agent execution"""
    PROMPT = "prompt"
    TOOL = "tool"
    SUBAGENT = "subagent"
    SYSTEM = "system"


class InvocationStatus(str, Enum):
    """Status of invocation or step"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class StepData:
    """ATP v0 Step schema"""
    step_id: str
    name: str
    kind: StepKind
    status: InvocationStatus
    start_ts: datetime
    end_ts: datetime
    latency_ms: int
    parent_step_id: Optional[str] = None
    model_provider: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_cents: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    input_excerpt: Optional[str] = None
    output_excerpt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to ATP v0 JSON format"""
        return {
            "step_id": self.step_id,
            "parent_step_id": self.parent_step_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_ts": self.start_ts.isoformat() + "Z" if self.start_ts.tzinfo is None else self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat() + "Z" if self.end_ts.tzinfo is None else self.end_ts.isoformat(),
            "latency_ms": self.latency_ms,
            "model_provider": self.model_provider,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_cents": self.cost_cents,
            "status": self.status.value,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "input_excerpt": self.input_excerpt,
            "output_excerpt": self.output_excerpt,
        }


@dataclass
class TraceData:
    """ATP v0 Trace schema"""
    trace_id: str
    invocation_id: str
    org_id: str
    project_id: str
    agent_id: str
    version_id: str
    start_ts: datetime
    end_ts: datetime
    status: InvocationStatus
    execution_time_ms: int
    cost_cents: int
    error_message: Optional[str] = None
    steps: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to ATP v0 JSON format"""
        return {
            "trace_id": self.trace_id,
            "invocation_id": self.invocation_id,
            "org_id": self.org_id,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "version_id": self.version_id,
            "start_ts": self.start_ts.isoformat() + "Z" if self.start_ts.tzinfo is None else self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat() + "Z" if self.end_ts.tzinfo is None else self.end_ts.isoformat(),
            "status": self.status.value,
            "execution_time_ms": self.execution_time_ms,
            "cost_cents": self.cost_cents,
            "error_message": self.error_message,
            "steps": [step.to_dict() if hasattr(step, 'to_dict') else step for step in self.steps],
        }
