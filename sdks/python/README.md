# AgentOS Python SDK

Span-level telemetry instrumentation for Model B agents to achieve **Verified Telemetry** badge.

## Installation

```bash
pip install agentos-sdk
```

## Quick Start

```python
from agentos_sdk import AgentOSClient

# Initialize client
client = AgentOSClient(
    api_url="https://api.agentos.example.com",
    api_key="your-api-key",
    agent_id="your-agent-id"
)

# Option 1: Decorator (simplest)
@client.instrument()
def my_agent(input_data):
    # Your agent logic here
    result = process(input_data)
    return result

# Option 2: Context manager (more control)
def my_agent_with_spans(input_data):
    with client.trace_invocation(input_data) as recorder:
        # Create custom spans
        with recorder.create_span("preprocessing", "system") as span:
            preprocessed = preprocess(input_data)
            span.set_io(input_data, preprocessed)

        # Track model calls
        with recorder.create_span("model.call", "prompt") as span:
            span.set_model("openai", "gpt-4o", {"temperature": 0.7})
            result = call_llm(preprocessed)
            span.set_io(preprocessed, result, tokens_in=100, tokens_out=50)
            span.set_cost(5)  # Cost in cents

        # Track tool calls
        with recorder.create_span("tool.search", "tool") as span:
            span.set_tool("search-123", "web_search", {"query": "..."})
            search_result = web_search(result)
            span.set_io({"query": result}, search_result)

        return search_result
```

## Features

### Automatic Span Recording
- **Prompt spans**: LLM calls with model params, tokens, cost
- **Tool spans**: Function/API calls with args and returns
- **System spans**: Processing steps and logic
- **Network spans**: Calls to other agents (A2A/MCP)

### W3C Trace Context Propagation
- `traceparent` header injection
- `baggage` for cross-cutting concerns
- Automatic parent-child span relationships

### Inter-Agent Communication
```python
# Call another agent with automatic edge tracking
result = client.call_agent(
    target_agent_id="agent-b",
    input_data={"query": "..."},
    protocol="a2a"
)
```

### Rich Span Metadata
```python
with recorder.create_span("custom", "system") as span:
    # Model information
    span.set_model("anthropic", "claude-3-opus", {"temperature": 1.0})

    # I/O tracking
    span.set_io(input_data, output_data, tokens_in=150, tokens_out=75)

    # Tool information
    span.set_tool("tool-id", "calculator", {"expr": "2+2"}, "4")

    # Cost tracking
    span.set_cost(10)  # 10 cents

    # Policy tracking
    span.set_policy(["policy-1"], obligations=["redact_pii"])

    # Custom metadata
    span.set_metadata("custom_field", "value")

    # Error handling
    try:
        result = risky_operation()
    except Exception as e:
        span.set_error(e)
        raise
```

## Span Kinds

- **`prompt`**: LLM inference calls
- **`tool`**: Function/API tool calls
- **`subagent`**: Calls to other agents
- **`system`**: Internal processing steps
- **`network`**: HTTP/gRPC calls

## Configuration

```python
client = AgentOSClient(
    api_url="https://api.agentos.example.com",
    api_key="your-api-key",
    agent_id="your-agent-id",
    version_id="v1.0",        # Optional
    auto_flush=True,          # Auto-send spans after invocation
    flush_interval=10,        # Flush interval in seconds
    debug=False               # Enable debug logging
)
```

## Advanced: Manual Span Flushing

```python
client = AgentOSClient(..., auto_flush=False)

with client.trace_invocation(input_data) as recorder:
    # ... your agent logic ...

    # Manually flush
    client.flush_spans(recorder)
```

## Benefits

✅ **Verified Telemetry Badge** - Full step-level visibility
✅ **Flamegraph Visualization** - Identify slow spans
✅ **Inter-Agent Sequence Diagrams** - Debug A2A/MCP flows
✅ **Deterministic Replay** - Reproduce bugs at span level
✅ **Anomaly Detection** - Prompt injection, tool abuse alerts
✅ **Cost Attribution** - Per-span cost tracking

## Examples

See `/examples` for:
- Simple agent with decorator
- Multi-step workflow with custom spans
- A2A agent-to-agent communication
- LangChain integration
- CrewAI integration

## License

Apache 2.0
