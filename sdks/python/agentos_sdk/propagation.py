"""
W3C Trace Context Propagation

Implements traceparent, tracestate, and baggage headers
for distributed tracing across agents.
"""

from typing import Dict, Optional, Tuple


class TraceContextPropagator:
    """W3C trace context propagation"""

    @staticmethod
    def create_traceparent(
        trace_id: str,
        span_id: str,
        sampled: bool = True
    ) -> str:
        """
        Create W3C traceparent header.

        Format: {version}-{trace_id}-{span_id}-{flags}
        Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
        """
        version = "00"
        flags = "01" if sampled else "00"

        # Normalize IDs
        trace_hex = trace_id.replace("-", "")[:32].zfill(32)
        span_hex = span_id.replace("-", "")[:16].zfill(16)

        return f"{version}-{trace_hex}-{span_hex}-{flags}"

    @staticmethod
    def parse_traceparent(traceparent: str) -> Tuple[str, str, bool]:
        """
        Parse W3C traceparent header.

        Returns: (trace_id, span_id, sampled)
        """
        parts = traceparent.split("-")
        if len(parts) != 4:
            raise ValueError(f"Invalid traceparent format: {traceparent}")

        version, trace_id, span_id, flags = parts

        if version != "00":
            raise ValueError(f"Unsupported traceparent version: {version}")

        sampled = flags.endswith("1")

        return trace_id, span_id, sampled

    @staticmethod
    def create_baggage(items: Dict[str, str]) -> str:
        """
        Create W3C baggage header.

        Format: key1=value1,key2=value2
        Example: agent_id=abc-123,version_id=v1.0
        """
        return ",".join(f"{k}={v}" for k, v in items.items() if v)

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

    def create_context(
        self,
        trace_id: str,
        span_id: Optional[str] = None,
        baggage: Optional[Dict[str, str]] = None,
        run_mode: str = "normal",
        config_hash: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Create full trace context.

        Returns dict suitable for API ingestion.
        """
        if not span_id:
            # Generate root span ID
            import uuid
            span_id = str(uuid.uuid4())

        traceparent = self.create_traceparent(trace_id, span_id, sampled=True)
        baggage_str = self.create_baggage(baggage or {})

        return {
            "traceparent": traceparent,
            "tracestate": "",  # Optional vendor-specific state
            "baggage": baggage or {},
            "run_mode": run_mode,
            "config_hash": config_hash
        }

    def inject_headers(
        self,
        headers: Dict[str, str],
        trace_id: str,
        parent_span_id: str,
        baggage: Optional[Dict[str, str]] = None
    ):
        """
        Inject W3C headers into HTTP request headers.

        propagator.inject_headers(
            headers,
            trace_id="...",
            parent_span_id="...",
            baggage={"agent_id": "..."}
        )
        """
        traceparent = self.create_traceparent(trace_id, parent_span_id)
        headers["traceparent"] = traceparent

        if baggage:
            headers["baggage"] = self.create_baggage(baggage)

    def extract_headers(self, headers: Dict[str, str]) -> Dict[str, any]:
        """
        Extract W3C context from HTTP headers.

        Returns: {trace_id, span_id, sampled, baggage}
        """
        traceparent = headers.get("traceparent", "")
        baggage_str = headers.get("baggage", "")

        if not traceparent:
            return {}

        trace_id, span_id, sampled = self.parse_traceparent(traceparent)
        baggage = self.parse_baggage(baggage_str) if baggage_str else {}

        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "sampled": sampled,
            "baggage": baggage
        }
