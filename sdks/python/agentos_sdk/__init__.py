"""
AgentOS Python SDK for Model B Agents

Provides span-level instrumentation for external agents to emit
ATP v0.1 telemetry and achieve "Verified Telemetry" badge.

Installation:
    pip install agentos-sdk

Usage:
    from agentos_sdk import AgentOSClient, span

    client = AgentOSClient(
        api_url="https://api.agentos.example.com",
        api_key="your-api-key",
        agent_id="your-agent-id"
    )

    @client.instrument()
    def my_agent_function(input_data):
        with span("processing", "system"):
            # Your agent logic
            with span("model.call", "prompt") as s:
                s.set_model("openai", "gpt-4o", {"temperature": 0.7})
                result = call_llm(prompt)
                s.set_io(prompt, result, tokens_in=100, tokens_out=50)
                s.set_cost(5)

            return result
"""

from .client import AgentOSClient
from .instrumentation import span, SpanRecorder
from .propagation import TraceContextPropagator
from .version import __version__

__all__ = [
    "AgentOSClient",
    "span",
    "SpanRecorder",
    "TraceContextPropagator",
    "__version__",
]
