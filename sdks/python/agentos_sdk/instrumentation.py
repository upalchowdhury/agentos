"""
Span instrumentation utilities for AgentOS SDK
"""

import hashlib
import json
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# Thread-local storage for current recorder
_current_recorder = threading.local()


@dataclass
class SpanData:
    """ATP v0.1 span data"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    invocation_id: str
    agent_id: str
    version_id: Optional[str]

    name: str
    kind: str
    start_ts: str
    end_ts: Optional[str] = None
    duration_ms: Optional[int] = None
    status: str = "running"

    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_params: Optional[Dict[str, Any]] = None

    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    input_excerpt: Optional[str] = None
    output_excerpt: Optional[str] = None
    content_hash_in: Optional[str] = None
    content_hash_out: Optional[str] = None
    signature_verified: bool = False

    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args_excerpt: Optional[str] = None
    tool_return_excerpt: Optional[str] = None

    policy_enforced: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    redaction_mask_ids: List[str] = field(default_factory=list)
    budget_enforced_cents: Optional[int] = None
    policy_allow: bool = True

    protocol: Optional[str] = None
    remote_agent_id: Optional[str] = None
    remote_version_id: Optional[str] = None
    request_id: Optional[str] = None
    edge_id: Optional[str] = None

    cost_cents: int = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    links: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Span:
    """Active span with convenience methods"""

    def __init__(self, data: SpanData, recorder: "SpanRecorder"):
        self.data = data
        self.recorder = recorder
        self._start_time = time.perf_counter()

    def set_model(self, provider: str, name: str, params: Optional[Dict] = None):
        """Set model information"""
        self.data.model_provider = provider
        self.data.model_name = name
        self.data.model_params = params or {}

    def set_io(
        self,
        input_data: Any,
        output_data: Any = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None
    ):
        """Set input/output with optional tokens"""
        self.data.input_excerpt = self._excerpt(input_data)
        if output_data is not None:
            self.data.output_excerpt = self._excerpt(output_data)

        self.data.tokens_in = tokens_in
        self.data.tokens_out = tokens_out

        self.data.content_hash_in = self._hash(input_data)
        if output_data is not None:
            self.data.content_hash_out = self._hash(output_data)

    def set_tool(self, call_id: str, name: str, args: Any = None, result: Any = None):
        """Set tool call information"""
        self.data.tool_call_id = call_id
        self.data.tool_name = name
        if args is not None:
            self.data.tool_args_excerpt = self._excerpt(args, max_len=256)
        if result is not None:
            self.data.tool_return_excerpt = self._excerpt(result, max_len=256)

    def set_network(
        self,
        protocol: str,
        remote_agent_id: str,
        request_id: Optional[str] = None,
        edge_id: Optional[str] = None
    ):
        """Set network call information"""
        self.data.protocol = protocol
        self.data.remote_agent_id = remote_agent_id
        self.data.request_id = request_id
        self.data.edge_id = edge_id

    def set_policy(self, policy_ids: List[str], obligations: Optional[List[str]] = None):
        """Set policy enforcement"""
        self.data.policy_enforced = policy_ids
        if obligations:
            self.data.obligations = obligations

    def add_redaction(self, mask_id: str):
        """Record redaction"""
        if mask_id not in self.data.redaction_mask_ids:
            self.data.redaction_mask_ids.append(mask_id)

    def set_cost(self, cost_cents: int):
        """Set cost"""
        self.data.cost_cents = cost_cents

    def set_error(self, error: Exception):
        """Record error"""
        self.data.status = "error"
        self.data.error_type = type(error).__name__
        self.data.error_message = str(error)

    def set_metadata(self, key: str, value: Any):
        """Add metadata"""
        self.data.metadata[key] = value

    def add_link(self, linked_span_id: str, link_type: str = "follows_from"):
        """Add span link"""
        self.data.links.append({
            "span_id": linked_span_id,
            "type": link_type,
            "attributes": {}
        })

    def finish(self, status: str = "success"):
        """Mark span complete"""
        self.data.end_ts = datetime.now(timezone.utc).isoformat()
        self.data.duration_ms = max(1, int((time.perf_counter() - self._start_time) * 1000))
        self.data.status = status
        self.recorder.record_span(self.data)

    @staticmethod
    def _excerpt(data: Any, max_len: int = 512) -> str:
        """Create excerpt"""
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
        """Compute SHA256 hash"""
        if isinstance(data, str):
            content = data.encode("utf-8")
        elif isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True).encode("utf-8")
        else:
            content = str(data).encode("utf-8")

        return hashlib.sha256(content).hexdigest()


class SpanRecorder:
    """Records spans in a trace"""

    def __init__(
        self,
        trace_id: str,
        invocation_id: str,
        agent_id: str,
        version_id: Optional[str] = None
    ):
        self.trace_id = trace_id
        self.invocation_id = invocation_id
        self.agent_id = agent_id
        self.version_id = version_id
        self.spans: List[SpanData] = []
        self._span_stack: List[str] = []

    @contextmanager
    def create_span(self, name: str, kind: str, parent_span_id: Optional[str] = None):
        """Create a span context"""
        span_id = str(uuid.uuid4())
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
            start_ts=datetime.now(timezone.utc).isoformat()
        )

        span = Span(span_data, self)
        self._span_stack.append(span_id)

        try:
            yield span
        except Exception as e:
            span.set_error(e)
            span.finish("error")
            raise
        finally:
            if span.data.status == "running":
                span.finish("success")
            self._span_stack.pop()

    def record_span(self, span_data: SpanData):
        """Record completed span"""
        self.spans.append(span_data)

    def get_spans(self) -> List[Dict[str, Any]]:
        """Get all spans as dicts"""
        return [asdict(s) for s in self.spans]


# Global convenience function
@contextmanager
def span(name: str, kind: str = "system"):
    """
    Convenient span context using thread-local recorder.

    with span("processing", "system"):
        ...
    """
    recorder = _current_recorder.__dict__.get("recorder")
    if recorder is None:
        # No-op if no active recorder
        yield None
        return

    with recorder.create_span(name, kind) as s:
        yield s
