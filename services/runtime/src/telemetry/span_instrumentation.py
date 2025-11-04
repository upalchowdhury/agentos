"""
Span-level instrumentation for ATP v0.1 telemetry.

Provides context managers and utilities for creating fine-grained spans
across prompts, tools, sub-agents, and network calls.

Usage:
    from telemetry.span_instrumentation import SpanRecorder, create_span

    recorder = SpanRecorder(trace_id, invocation_id, agent_id)

    with recorder.create_span("model.call", "prompt") as span:
        span.set_model("openai", "gpt-4o", {"temperature": 0.7, "seed": 42})
        result = call_llm(prompt)
        span.set_io(prompt, result, tokens_in=100, tokens_out=50)
        span.set_cost(cost_cents=5)
"""

import hashlib
import json
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SpanData:
    """ATP v0.1 span data structure"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    invocation_id: str
    agent_id: str
    version_id: Optional[str]

    name: str
    kind: str  # prompt, tool, subagent, system, network
    start_ts: datetime
    end_ts: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "running"  # running, success, error, timeout, cancelled

    # Model info (for prompt spans)
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_params: Optional[Dict[str, Any]] = None

    # I/O
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    input_excerpt: Optional[str] = None
    output_excerpt: Optional[str] = None
    content_hash_in: Optional[str] = None
    content_hash_out: Optional[str] = None
    signature_verified: bool = False

    # Tool info (for tool spans)
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args_excerpt: Optional[str] = None
    tool_return_excerpt: Optional[str] = None

    # Policy
    policy_enforced: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    redaction_mask_ids: List[str] = field(default_factory=list)
    budget_enforced_cents: Optional[int] = None
    policy_allow: bool = True

    # Network (for subagent/network spans)
    protocol: Optional[str] = None  # a2a, mcp, http, grpc, none
    remote_agent_id: Optional[str] = None
    remote_version_id: Optional[str] = None
    request_id: Optional[str] = None
    edge_id: Optional[str] = None

    # Cost & errors
    cost_cents: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    # Links (OTel span links)
    links: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class Span:
    """Active span context with convenient setters"""

    def __init__(self, data: SpanData, recorder: "SpanRecorder"):
        self.data = data
        self.recorder = recorder
        self._start_time = time.perf_counter()

    def set_model(self, provider: str, name: str, params: Optional[Dict] = None):
        """Set model information for prompt spans"""
        self.data.model_provider = provider
        self.data.model_name = name
        self.data.model_params = params or {}

    def set_io(
        self,
        input_data: Any,
        output_data: Any = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        compute_hash: bool = True
    ):
        """Set input/output with optional token counts and hashing"""
        self.data.input_excerpt = self._excerpt(input_data, max_len=512)
        if output_data is not None:
            self.data.output_excerpt = self._excerpt(output_data, max_len=512)

        self.data.tokens_in = tokens_in
        self.data.tokens_out = tokens_out

        if compute_hash:
            self.data.content_hash_in = self._hash(input_data)
            if output_data is not None:
                self.data.content_hash_out = self._hash(output_data)

    def set_tool(self, call_id: str, name: str, args: Any = None, return_value: Any = None):
        """Set tool call information"""
        self.data.tool_call_id = call_id
        self.data.tool_name = name
        if args is not None:
            self.data.tool_args_excerpt = self._excerpt(args, max_len=256)
        if return_value is not None:
            self.data.tool_return_excerpt = self._excerpt(return_value, max_len=256)

    def set_network(
        self,
        protocol: str,
        remote_agent_id: str,
        request_id: Optional[str] = None,
        edge_id: Optional[str] = None
    ):
        """Set network/subagent call information"""
        self.data.protocol = protocol
        self.data.remote_agent_id = remote_agent_id
        self.data.request_id = request_id
        self.data.edge_id = edge_id

    def set_policy(
        self,
        policy_ids: List[str],
        obligations: Optional[List[str]] = None,
        allow: bool = True
    ):
        """Set policy enforcement results"""
        self.data.policy_enforced = policy_ids
        if obligations:
            self.data.obligations = obligations
        self.data.policy_allow = allow

    def add_redaction(self, mask_id: str):
        """Record redaction mask applied"""
        if mask_id not in self.data.redaction_mask_ids:
            self.data.redaction_mask_ids.append(mask_id)

    def set_cost(self, cost_cents: int):
        """Set span cost"""
        self.data.cost_cents = cost_cents

    def set_budget_enforced(self, budget_cents: int):
        """Record budget cap enforcement"""
        self.data.budget_enforced_cents = budget_cents

    def add_link(self, linked_span_id: str, link_type: str = "follows_from", attributes: Optional[Dict] = None):
        """Add OTel span link"""
        self.data.links.append({
            "span_id": linked_span_id,
            "type": link_type,
            "attributes": attributes or {}
        })

    def set_error(self, error: Exception):
        """Record error information"""
        self.data.status = "error"
        self.data.error_type = type(error).__name__
        self.data.error_message = str(error)

    def set_metadata(self, key: str, value: Any):
        """Add custom metadata"""
        self.data.metadata[key] = value

    def finish(self, status: str = "success"):
        """Mark span as complete"""
        self.data.end_ts = datetime.now(timezone.utc)
        self.data.duration_ms = max(1, int((time.perf_counter() - self._start_time) * 1000))
        self.data.status = status
        self.recorder.record_span(self.data)

    @staticmethod
    def _excerpt(data: Any, max_len: int = 512) -> str:
        """Create excerpt from data"""
        if data is None:
            return ""

        if isinstance(data, str):
            text = data
        elif isinstance(data, (dict, list)):
            text = json.dumps(data)
        else:
            text = str(data)

        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    @staticmethod
    def _hash(data: Any) -> str:
        """Compute SHA256 hash of data"""
        if isinstance(data, str):
            content = data.encode("utf-8")
        elif isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True).encode("utf-8")
        else:
            content = str(data).encode("utf-8")

        return hashlib.sha256(content).hexdigest()


class SpanRecorder:
    """Records spans and manages span hierarchy"""

    def __init__(
        self,
        trace_id: str,
        invocation_id: str,
        agent_id: str,
        version_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ):
        self.trace_id = trace_id
        self.invocation_id = invocation_id
        self.agent_id = agent_id
        self.version_id = version_id
        self.current_span_id = parent_span_id
        self.spans: List[SpanData] = []
        self._span_stack: List[str] = []

    @contextmanager
    def create_span(self, name: str, kind: str, parent_span_id: Optional[str] = None):
        """Create a new span context"""
        span_id = str(uuid.uuid4())

        # Use explicit parent or current span from stack
        parent = parent_span_id or (self._span_stack[-1] if self._span_stack else None)

        span_data = SpanData(
            span_id=span_id,
            trace_id=self.trace_id,
            parent_span_id=parent,
            invocation_id=self.invocation_id,
            agent_id=self.agent_id,
            version_id=self.version_id,
            name=name,
            kind=kind,
            start_ts=datetime.now(timezone.utc)
        )

        span = Span(span_data, self)
        self._span_stack.append(span_id)

        try:
            yield span
            span.finish("success")
        except Exception as e:
            span.set_error(e)
            span.finish("error")
            raise
        finally:
            self._span_stack.pop()

    def record_span(self, span_data: SpanData):
        """Record a completed span"""
        self.spans.append(span_data)
        logger.debug(
            f"Span recorded: {span_data.name} ({span_data.kind}) "
            f"duration={span_data.duration_ms}ms status={span_data.status}"
        )

    def get_spans(self) -> List[Dict[str, Any]]:
        """Get all recorded spans as dicts"""
        return [self._span_to_dict(s) for s in self.spans]

    @staticmethod
    def _span_to_dict(span: SpanData) -> Dict[str, Any]:
        """Convert SpanData to dictionary"""
        d = asdict(span)
        # Convert datetime to ISO format
        if d.get("start_ts"):
            d["start_ts"] = d["start_ts"].isoformat()
        if d.get("end_ts"):
            d["end_ts"] = d["end_ts"].isoformat()
        return d


class SpanPropagator:
    """W3C trace context propagation (traceparent, tracestate)"""

    @staticmethod
    def create_traceparent(trace_id: str, span_id: str, sampled: bool = True) -> str:
        """Create W3C traceparent header

        Format: {version}-{trace_id}-{span_id}-{flags}
        Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
        """
        version = "00"
        flags = "01" if sampled else "00"

        # Pad/truncate to correct lengths
        trace_hex = trace_id.replace("-", "")[:32].zfill(32)
        span_hex = span_id.replace("-", "")[:16].zfill(16)

        return f"{version}-{trace_hex}-{span_hex}-{flags}"

    @staticmethod
    def parse_traceparent(traceparent: str) -> Tuple[str, str, bool]:
        """Parse W3C traceparent header

        Returns: (trace_id, span_id, sampled)
        """
        parts = traceparent.split("-")
        if len(parts) != 4:
            raise ValueError(f"Invalid traceparent format: {traceparent}")

        version, trace_id, span_id, flags = parts

        if version != "00":
            logger.warning(f"Unsupported traceparent version: {version}")

        sampled = flags.endswith("1")

        return trace_id, span_id, sampled

    @staticmethod
    def create_baggage(items: Dict[str, str]) -> str:
        """Create W3C baggage header

        Format: key1=value1,key2=value2
        Example: agent_id=abc-123,version_id=v1.0,run_mode=deterministic
        """
        return ",".join(f"{k}={v}" for k, v in items.items())

    @staticmethod
    def parse_baggage(baggage: str) -> Dict[str, str]:
        """Parse W3C baggage header"""
        items = {}
        for pair in baggage.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                items[k.strip()] = v.strip()
        return items


# Global span context (thread-local in production)
_current_recorder: Optional[SpanRecorder] = None


def set_current_recorder(recorder: SpanRecorder):
    """Set the active span recorder"""
    global _current_recorder
    _current_recorder = recorder


def get_current_recorder() -> Optional[SpanRecorder]:
    """Get the active span recorder"""
    return _current_recorder


@contextmanager
def span_context(name: str, kind: str):
    """Convenient context manager using global recorder"""
    recorder = get_current_recorder()
    if recorder is None:
        # No-op if no recorder active
        yield None
        return

    with recorder.create_span(name, kind) as span:
        yield span
