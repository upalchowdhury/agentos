"""
AgentOS Client for Model B agents
"""

import functools
import json
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import requests

from .instrumentation import SpanRecorder, _current_recorder
from .propagation import TraceContextPropagator

logger = logging.getLogger(__name__)


class AgentOSClient:
    """
    Client for AgentOS API with automatic span instrumentation.

    Usage:
        client = AgentOSClient(
            api_url="https://api.agentos.example.com",
            api_key="your-api-key",
            agent_id="your-agent-id",
            version_id="v1.0"  # optional
        )

        # Option 1: Decorator
        @client.instrument()
        def my_function(input_data):
            ...

        # Option 2: Context manager
        with client.trace_invocation(input_data) as recorder:
            with recorder.create_span("step1", "system"):
                ...
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        agent_id: str,
        agent_name: str = "unknown-agent",
        platform: str = "python-sdk",
        version_id: Optional[str] = None,
        auto_flush: bool = True,
        flush_interval: int = 10,
        debug: bool = False
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.platform = platform
        self.version_id = version_id
        self.auto_flush = auto_flush
        self.flush_interval = flush_interval
        self.debug = debug

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"AgentOS-SDK-Python/{self._get_version()}"
        })

        self.propagator = TraceContextPropagator()

        if debug:
            logging.basicConfig(level=logging.DEBUG)
            logger.setLevel(logging.DEBUG)

    def instrument(self, name: Optional[str] = None):
        """
        Decorator to instrument a function with automatic tracing.

        @client.instrument()
        def my_agent(input_data):
            # Automatically creates invocation trace
            return process(input_data)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_name = name or func.__name__
                input_data = self._extract_input(args, kwargs)

                with self.trace_invocation(input_data, name=func_name) as recorder:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        logger.error(f"Function {func_name} failed: {e}")
                        raise

            return wrapper
        return decorator

    @contextmanager
    def trace_invocation(
        self,
        input_data: Any,
        name: Optional[str] = None,
        invocation_id: Optional[str] = None
    ):
        """
        Context manager for tracing an invocation with span recording.

        with client.trace_invocation(input_data) as recorder:
            with recorder.create_span("process", "system") as span:
                ...
        """
        # Create invocation ID and trace ID
        invocation_id = invocation_id or str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        # Create span recorder
        recorder = SpanRecorder(
            trace_id=trace_id,
            invocation_id=invocation_id,
            agent_id=self.agent_id,
            version_id=self.version_id
        )

        # Set as current recorder (thread-local)
        _current_recorder.recorder = recorder

        # Create root span
        root_span_name = name or "invocation"
        with recorder.create_span(root_span_name, "system") as root_span:
            root_span.set_metadata("input_excerpt", self._excerpt(input_data))

            try:
                yield recorder
                root_span.finish("success")
            except Exception as e:
                root_span.set_error(e)
                root_span.finish("error")
                raise
            finally:
                # Flush spans to AgentOS
                if self.auto_flush:
                    self.flush_spans(recorder)

                # Clear current recorder
                _current_recorder.recorder = None

    def flush_spans(self, recorder: SpanRecorder):
        """Send recorded spans to AgentOS API via unified ingestion"""
        spans = recorder.get_spans()

        if not spans:
            logger.debug("No spans to flush")
            return

        events = []
        for span in spans:
            # Map SpanData to AgentExecution schema
            event = {
                "id": str(uuid.uuid4()),
                "platform": self.platform,
                "tenantId": "default",  # Should be inferred by API key usually
                "timestamp": span.get("end_ts") or span.get("start_ts"),
                "agent": {
                    "id": self.agent_id,
                    "name": self.agent_name,
                    "version": self.version_id or "v0",
                    "type": "conversational"  # Default
                },
                "execution": {
                    "traceId": span["trace_id"],
                    "spanId": span["span_id"],
                    "parentSpanId": span.get("parent_span_id"),
                    "durationMs": span.get("duration_ms", 0),
                    "status": span.get("status", "unknown")
                },
                "context": {
                    "environment": "production",  # Could be parameterized
                    "tags": span.get("metadata", {})
                }
            }

            # Add LLM data if present
            if span.get("model_name"):
                event["llm"] = {
                    "provider": span.get("model_provider", "unknown"),
                    "model": span.get("model_name"),
                    "inputTokens": span.get("tokens_in", 0),
                    "outputTokens": span.get("tokens_out", 0),
                    "totalCostUsd": (span.get("cost_cents", 0) or 0) / 100.0
                }

            # Add IO data
            if span.get("input_excerpt") or span.get("output_excerpt"):
                event["io"] = {
                    "input": span.get("input_excerpt"),
                    "output": span.get("output_excerpt"),
                    "piiDetected": False  # SDK doesn't detect PII yet
                }

            events.append(event)

        payload = {"events": events}

        try:
            response = self.session.post(
                f"{self.api_url}/v1/telemetry/events",
                json=payload,
                timeout=5
            )

            if response.status_code >= 300:
                logger.error(
                    f"Failed to flush events: HTTP {response.status_code} - {response.text}"
                )
            else:
                result = response.json()
                logger.info(
                    f"Flushed {result.get('accepted', 0)} events for trace {recorder.trace_id}"
                )

        except Exception as e:
            logger.error(f"Error flushing events: {e}")

    def create_edge(
        self,
        from_span_id: str,
        to_agent_id: str,
        to_span_id: str,
        channel: str = "http",
        instruction_type: str = "prompt",
        metadata: Optional[Dict] = None
    ):
        """
        Record an inter-agent edge (for A2A/MCP calls).

        client.create_edge(
            from_span_id=current_span_id,
            to_agent_id="target-agent-id",
            to_span_id=remote_span_id,
            channel="a2a",
            instruction_type="tool_request"
        )
        """
        recorder = _current_recorder.get()
        if not recorder:
            logger.warning("No active recorder for edge creation")
            return

        edge = {
            "edge_id": str(uuid.uuid4()),
            "trace_id": recorder.trace_id,
            "from_agent_id": self.agent_id,
            "from_version_id": self.version_id,
            "from_span_id": from_span_id,
            "to_agent_id": to_agent_id,
            "to_span_id": to_span_id,
            "channel": channel,
            "instruction_type": instruction_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }

        payload = {"edges": [edge]}

        try:
            response = self.session.post(
                f"{self.api_url}/v1/spans/edges/ingest",
                json=payload,
                timeout=5
            )

            if response.status_code >= 300:
                logger.error(f"Failed to create edge: HTTP {response.status_code}")
            else:
                logger.debug(f"Created edge {edge['edge_id']}")

        except Exception as e:
            logger.error(f"Error creating edge: {e}")

    def call_agent(
        self,
        target_agent_id: str,
        input_data: Dict[str, Any],
        protocol: str = "a2a"
    ) -> Dict[str, Any]:
        """
        Call another agent and automatically create edge tracking.

        result = client.call_agent(
            target_agent_id="other-agent",
            input_data={"query": "..."},
            protocol="a2a"
        )
        """
        recorder = _current_recorder.get()
        if not recorder:
            raise RuntimeError("call_agent must be used within trace_invocation context")

        # Create network span
        with recorder.create_span(f"call_agent.{target_agent_id}", "network") as span:
            span.set_network(protocol, target_agent_id)
            span.set_io(input_data)

            # Make API call to target agent via gateway
            endpoint = f"{self.api_url}/v1/agents/{target_agent_id}/invoke"

            # Propagate trace context
            headers = {}
            self.propagator.inject_headers(
                headers,
                trace_id=recorder.trace_id,
                parent_span_id=span.data.span_id,
                baggage={
                    "agent_id": self.agent_id,
                    "version_id": self.version_id or "",
                }
            )

            try:
                response = self.session.post(
                    endpoint,
                    json={"input": input_data},
                    headers=headers,
                    timeout=30
                )

                if response.status_code >= 300:
                    span.set_error(Exception(f"HTTP {response.status_code}"))
                    span.finish("error")
                    raise Exception(f"Agent call failed: HTTP {response.status_code}")

                result = response.json()
                span.set_io(input_data, result)
                span.set_metadata("http_status", response.status_code)

                # Extract remote span ID if available
                remote_span_id = response.headers.get("x-agentos-span-id")
                if remote_span_id:
                    # Create edge
                    self.create_edge(
                        from_span_id=span.data.span_id,
                        to_agent_id=target_agent_id,
                        to_span_id=remote_span_id,
                        channel=protocol,
                        instruction_type="prompt"
                    )

                span.finish("success")
                return result

            except Exception as e:
                span.set_error(e)
                span.finish("error")
                raise

    @staticmethod
    def _extract_input(args: tuple, kwargs: dict) -> Any:
        """Extract input data from function args/kwargs"""
        if args:
            return args[0]
        if "input" in kwargs:
            return kwargs["input"]
        if "input_data" in kwargs:
            return kwargs["input_data"]
        if "data" in kwargs:
            return kwargs["data"]
        return kwargs

    @staticmethod
    def _excerpt(data: Any, max_len: int = 256) -> str:
        """Create excerpt from data"""
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
    def _get_version() -> str:
        """Get SDK version"""
        try:
            from .version import __version__
            return __version__
        except ImportError:
            return "unknown"
