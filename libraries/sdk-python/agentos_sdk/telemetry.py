"""Telemetry builders for AgentOS SDK"""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .models import StepData, StepKind, InvocationStatus, TraceData


class StepBuilder:
    """Builder for step-level telemetry"""

    def __init__(
        self,
        name: str,
        kind: StepKind,
        parent_step_id: Optional[str] = None,
    ):
        self.step_id = f"step-{uuid.uuid4().hex[:12]}"
        self.name = name
        self.kind = kind
        self.parent_step_id = parent_step_id
        self.start_time = time.time()
        self.start_ts = datetime.now(timezone.utc)
        self.end_ts: Optional[datetime] = None
        self.latency_ms: Optional[int] = None
        self.status = InvocationStatus.SUCCESS
        self.model_provider: Optional[str] = None
        self.tokens_in: Optional[int] = None
        self.tokens_out: Optional[int] = None
        self.cost_cents: Optional[int] = None
        self.error_type: Optional[str] = None
        self.error_message: Optional[str] = None
        self.input_excerpt: Optional[str] = None
        self.output_excerpt: Optional[str] = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-finalize"""
        if exc_type is not None:
            self.fail(error_type=exc_type.__name__, error_message=str(exc_val))
        else:
            self.finish()
        return False

    def set_model(self, provider: str, tokens_in: int = 0, tokens_out: int = 0) -> "StepBuilder":
        """Set model provider and token usage"""
        self.model_provider = provider
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        return self

    def set_cost(self, cents: int) -> "StepBuilder":
        """Set step cost in cents"""
        self.cost_cents = cents
        return self

    def set_input(self, excerpt: str, max_length: int = 500) -> "StepBuilder":
        """Set input excerpt (truncated)"""
        self.input_excerpt = excerpt[:max_length] if len(excerpt) > max_length else excerpt
        return self

    def set_output(self, excerpt: str, max_length: int = 500) -> "StepBuilder":
        """Set output excerpt (truncated)"""
        self.output_excerpt = excerpt[:max_length] if len(excerpt) > max_length else excerpt
        return self

    def fail(self, error_type: str, error_message: str) -> "StepBuilder":
        """Mark step as failed"""
        self.status = InvocationStatus.ERROR
        self.error_type = error_type
        self.error_message = error_message
        return self

    def finish(self) -> StepData:
        """Finalize step and return data"""
        self.end_ts = datetime.now(timezone.utc)
        self.latency_ms = int((time.time() - self.start_time) * 1000)
        
        return StepData(
            step_id=self.step_id,
            parent_step_id=self.parent_step_id,
            name=self.name,
            kind=self.kind,
            start_ts=self.start_ts,
            end_ts=self.end_ts,
            latency_ms=self.latency_ms,
            status=self.status,
            model_provider=self.model_provider,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            cost_cents=self.cost_cents,
            error_type=self.error_type,
            error_message=self.error_message,
            input_excerpt=self.input_excerpt,
            output_excerpt=self.output_excerpt,
        )


class TelemetryBuilder:
    """Builder for invocation-level telemetry (ATP v0)"""

    def __init__(
        self,
        org_id: str,
        project_id: str,
        agent_id: str,
        version_id: str = "v1",
    ):
        self.trace_id = f"trace-{uuid.uuid4().hex}"
        self.invocation_id = f"inv-{uuid.uuid4().hex}"
        self.org_id = org_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.version_id = version_id
        self.start_time = time.time()
        self.start_ts = datetime.now(timezone.utc)
        self.end_ts: Optional[datetime] = None
        self.execution_time_ms: Optional[int] = None
        self.status = InvocationStatus.SUCCESS
        self.error_message: Optional[str] = None
        self.steps: list = []
        self.total_cost_cents = 0

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-finalize"""
        if exc_type is not None:
            self.fail(str(exc_val))
        else:
            self.finish()
        return False

    def add_step(self, step: StepData) -> "TelemetryBuilder":
        """Add completed step to trace"""
        self.steps.append(step)
        if step.cost_cents:
            self.total_cost_cents += step.cost_cents
        return self

    def step(
        self,
        name: str,
        kind: StepKind,
        parent_step_id: Optional[str] = None,
    ) -> StepBuilder:
        """Create new step builder"""
        return StepBuilder(name=name, kind=kind, parent_step_id=parent_step_id)

    def fail(self, error_message: str) -> "TelemetryBuilder":
        """Mark invocation as failed"""
        self.status = InvocationStatus.ERROR
        self.error_message = error_message
        return self

    def finish(self) -> TraceData:
        """Finalize trace and return data"""
        self.end_ts = datetime.now(timezone.utc)
        self.execution_time_ms = int((time.time() - self.start_time) * 1000)
        
        return TraceData(
            trace_id=self.trace_id,
            invocation_id=self.invocation_id,
            org_id=self.org_id,
            project_id=self.project_id,
            agent_id=self.agent_id,
            version_id=self.version_id,
            start_ts=self.start_ts,
            end_ts=self.end_ts,
            status=self.status,
            execution_time_ms=self.execution_time_ms,
            cost_cents=self.total_cost_cents,
            error_message=self.error_message,
            steps=self.steps,
        )
