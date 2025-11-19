# Build & Monitor Agents with AgentOS

This guide explains how to build agents using the Python SDK or LangChain and monitor them in the AgentOS platform.

## Prerequisites

- AgentOS running locally (`./run-app.sh` for UI, `docker-compose up` for backend)
- Python 3.9+
- `agentos-sdk` installed

## Option 1: Using LangChain

We provide a native `CallbackHandler` for seamless integration.

### 1. Install SDK
```bash
pip install agentos-sdk
```

### 2. Instrument your Agent
```python
from agentos_sdk.client import AgentOSClient
from agentos_sdk.langchain import AgentOSCallbackHandler
from langchain.agents import initialize_agent, load_tools
from langchain.llms import OpenAI

# Initialize Client
client = AgentOSClient(
    api_url="http://localhost:8000",
    api_key="your-api-key",
    agent_id="my-langchain-agent"
)

# Create Callback
cb = AgentOSCallbackHandler(client)

# Run Agent
llm = OpenAI(temperature=0)
agent = initialize_agent(..., llm=llm)

agent.run("Hello world", callbacks=[cb])

# Flush traces
cb.flush()
```

## Option 2: Native Python SDK

For custom agents not using LangChain.

```python
from agentos_sdk.client import AgentOSClient

client = AgentOSClient(
    api_url="http://localhost:8000",
    api_key="your-api-key",
    agent_id="my-custom-agent"
)

@client.instrument()
def my_agent_task(input_data):
    # Your logic here
    return "result"

my_agent_task("some input")
```

## Viewing Telemetry

1. Go to **http://localhost:3001/traces**
2. You will see your agent's execution traces, including:
   - **Latency & Cost**
   - **LLM Inputs/Outputs**
   - **Tool Usage**
   - **Policy Checks**

## Backend Status

Currently, the **UI is running in demo mode** with mock data. To enable real ingestion:

1. Start the full backend stack:
   ```bash
   docker-compose -f docker-compose.dev.yaml up -d
   ```
2. Ensure the `ingest` service is running on port 8003 (mapped to 8000 in some configs).
3. Update your `AgentOSClient` `api_url` to point to the ingest service.
