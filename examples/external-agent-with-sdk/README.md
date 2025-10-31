# Example: External Agent with AgentOS SDK

This example demonstrates how to build an external agent (Model B) that integrates with AgentOS using the Python SDK for **verified telemetry**.

## Features Demonstrated

✅ **US-B2**: SDK for deep telemetry with verified badge  
✅ **ATP v0 Protocol**: Step-level traces with timing, costs, tokens  
✅ **Context Managers**: Automatic telemetry tracking  
✅ **Error Handling**: Failed steps automatically captured  
✅ **Cost Attribution**: Per-step cost tracking  

## Quick Start

### 1. Install Dependencies

```bash
cd examples/external-agent-with-sdk
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export AGENTOS_URL="http://localhost:8000"
export AGENTOS_API_KEY="your-api-key"
export AGENTOS_ORG_ID="org-123"
export AGENTOS_PROJECT_ID="proj-456"
export AGENTOS_OWNER_ID="user-789"
export AGENT_ENDPOINT="http://localhost:8001/invoke"
```

### 3. Start the Agent

```bash
python main.py
```

Agent runs on `http://localhost:8001`

### 4. Register with AgentOS

```bash
curl -X POST http://localhost:8001/register
```

This creates a Model B agent in AgentOS platform.

### 5. Invoke the Agent

```bash
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "context": {}
  }'
```

### 6. View Telemetry in AgentOS

Visit AgentOS UI:
- **Dashboard**: See invocations with **Verified Telemetry** badge
- **Trace Viewer**: Drill down into step-level execution
- **Logs**: Correlated by `trace_id`
- **Metrics**: p95 latency, cost breakdown

## Architecture

```
┌─────────────────────────────────────┐
│   External Agent (FastAPI)          │
│   - Receives /invoke requests       │
│   - Uses AgentOS SDK                │
│   - Emits ATP v0 traces             │
└──────────────┬──────────────────────┘
               │ HTTP POST /v1/telemetry/ingest
               ▼
┌─────────────────────────────────────┐
│   AgentOS Platform                   │
│   - Receives telemetry               │
│   - Stores traces in DB              │
│   - Marks as 'verified'              │
│   - Shows in UI                      │
└─────────────────────────────────────┘
```

## Telemetry Flow

1. **Request arrives** → Create telemetry context
2. **Execute steps** → Each step tracked with timing
3. **Capture costs** → Token usage & cost per step
4. **Handle errors** → Failed steps marked automatically
5. **Auto-send** → ATP v0 trace sent on context exit
6. **Verified badge** → Displayed in AgentOS UI

## Code Walkthrough

### Create Telemetry Context

```python
with client.trace(
    org_id=org_id,
    project_id=project_id,
    agent_id=agent_id,
    auto_send=True
) as telemetry:
    # Your agent logic here
    # Telemetry auto-sent on exit
```

### Track Steps

```python
with telemetry.step("llm_call", StepKind.PROMPT) as step:
    result = call_llm(prompt)
    
    step.set_model("openai-gpt4", tokens_in=100, tokens_out=200)
    step.set_cost(15)  # cents
    step.set_input(prompt[:500])
    step.set_output(result[:500])
```

### Error Handling

```python
with telemetry.step("risky_operation", StepKind.TOOL) as step:
    try:
        result = risky_api_call()
    except Exception as e:
        # Step automatically marked as ERROR with exception details
        raise
```

## ATP v0 Trace Example

The SDK sends this format:

```json
{
  "trace_id": "trace-abc123xyz",
  "invocation_id": "inv-def456ghi",
  "org_id": "org-123",
  "project_id": "proj-456",
  "agent_id": "agent-789",
  "version_id": "v1.0",
  "start_ts": "2025-10-30T10:00:00Z",
  "end_ts": "2025-10-30T10:00:02Z",
  "status": "success",
  "execution_time_ms": 2000,
  "cost_cents": 25,
  "steps": [
    {
      "step_id": "step-001",
      "name": "generate_response",
      "kind": "prompt",
      "start_ts": "2025-10-30T10:00:00.500Z",
      "end_ts": "2025-10-30T10:00:01.500Z",
      "latency_ms": 1000,
      "model_provider": "openai-gpt4",
      "tokens_in": 50,
      "tokens_out": 150,
      "cost_cents": 15,
      "status": "success"
    }
  ]
}
```

## Benefits of SDK Integration

### Without SDK (Partial Telemetry)
- ❌ Only request/response times
- ❌ No step-level visibility
- ❌ No cost attribution
- ❌ Limited debugging

### With SDK (Verified Telemetry)
- ✅ Step-level execution graph
- ✅ Per-step timing & costs
- ✅ Token usage tracking
- ✅ Error localization
- ✅ Full observability

## Next Steps

1. **Adapt to your framework**: Integrate SDK into LangChain, CrewAI, etc.
2. **Add custom steps**: Track your specific operations
3. **Monitor in production**: Use AgentOS dashboard for alerts
4. **Optimize costs**: Identify expensive steps

## Troubleshooting

### Telemetry not appearing in AgentOS

- Check `AGENTOS_URL` points to running platform
- Verify `AGENTOS_API_KEY` is valid
- Ensure agent is registered (`POST /register`)
- Check runtime service logs for ingest errors

### "Agent not found" error

- Run registration endpoint first: `POST /register`
- Use returned `agent_id` in environment variables

## Learn More

- [SDK Documentation](../../libraries/sdk-python/README.md)
- [ATP v0 Specification](../../docs/ATP_SPEC.md)
- [PRD User Stories](../../PRD.md) - See US-B2 for requirements
