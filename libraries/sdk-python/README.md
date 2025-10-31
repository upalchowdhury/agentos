# AgentOS Python SDK

Python SDK for integrating external agents with AgentOS platform (Model B). Enables **verified telemetry** with Agent Telemetry Protocol (ATP) v0.

## Installation

```bash
pip install agentos-sdk
```

## Quick Start

### Register Your Agent

```python
from agentos_sdk import AgentOSClient

client = AgentOSClient(
    base_url="https://agentos.example.com",
    api_key="your-agent-token"
)

# Register as Model B agent
agent = client.register_agent(
    name="my-external-agent",
    endpoint="https://my-agent.example.com/invoke",
    owner_id="user-123",
    description="My external LangChain agent",
    metadata={"framework": "langchain", "version": "0.1.0"}
)

print(f"Agent registered: {agent['agent_id']}")
```

### Send Telemetry (ATP v0)

```python
from agentos_sdk import AgentOSClient, StepKind

with AgentOSClient(
    base_url="https://agentos.example.com",
    api_key="your-agent-token"
) as client:
    
    # Start invocation trace
    with client.trace(
        org_id="org-123",
        project_id="proj-456",
        agent_id="agent-789"
    ) as telemetry:
        
        # Step 1: Call LLM
        with telemetry.step("generate_response", StepKind.PROMPT) as step:
            response = llm.generate("What is AI?")
            step.set_model("openai", tokens_in=15, tokens_out=250)
            step.set_cost(5)  # 5 cents
            step.set_input("What is AI?")
            step.set_output(response[:500])
        
        # Step 2: Call tool
        with telemetry.step("search_docs", StepKind.TOOL) as step:
            docs = search_engine.query("AI definition")
            step.set_input("AI definition")
            step.set_output(f"Found {len(docs)} documents")
        
        # Telemetry auto-sent on exit with 'verified' badge
```

### Manual Telemetry

```python
from agentos_sdk import TelemetryBuilder, StepKind, InvocationStatus

# Build trace manually
telemetry = TelemetryBuilder(
    org_id="org-123",
    project_id="proj-456",
    agent_id="agent-789"
)

# Add steps
step = telemetry.step("process", StepKind.SYSTEM).finish()
telemetry.add_step(step)

# Finalize and send
trace = telemetry.finish()
client.send_telemetry(trace)
```

## Features

✅ **Verified Telemetry Badge** - Step-level traces visible in AgentOS UI  
✅ **ATP v0 Compliant** - Standard telemetry format  
✅ **Context Managers** - Automatic timing and error handling  
✅ **Cost Tracking** - Per-step cost attribution  
✅ **Token Counting** - LLM usage metrics  
✅ **Type Safe** - Full type hints with Python 3.9+

## ATP v0 Schema

The SDK implements Agent Telemetry Protocol v0:

```python
{
  "trace_id": "trace-abc123",
  "invocation_id": "inv-xyz789",
  "agent_id": "agent-789",
  "status": "success",
  "execution_time_ms": 1234,
  "cost_cents": 15,
  "steps": [
    {
      "step_id": "step-001",
      "name": "llm_call",
      "kind": "prompt",
      "start_ts": "2025-10-30T10:00:00Z",
      "end_ts": "2025-10-30T10:00:01Z",
      "latency_ms": 1000,
      "model_provider": "openai",
      "tokens_in": 100,
      "tokens_out": 200,
      "cost_cents": 10,
      "status": "success"
    }
  ]
}
```

## Error Handling

```python
with client.trace(...) as telemetry:
    with telemetry.step("risky_operation", StepKind.TOOL) as step:
        try:
            result = risky_call()
        except Exception as e:
            step.fail(error_type="APIError", error_message=str(e))
            raise
```

## Advanced Usage

### Parent-Child Steps

```python
with telemetry.step("orchestration", StepKind.SYSTEM) as parent:
    parent_id = parent.step_id
    
    # Child step
    with telemetry.step("subprocess", StepKind.TOOL, parent_step_id=parent_id) as child:
        child.set_output("subprocess complete")
```

### Disable Auto-Send

```python
with client.trace(..., auto_send=False) as telemetry:
    # ... build trace ...
    
    # Manually send later
    if should_send:
        telemetry.send_now()
```

## Requirements

- Python 3.9+
- httpx >= 0.25.0

## License

Apache 2.0
