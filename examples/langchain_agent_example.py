import os
import uuid
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.llms import FakeListLLM
from agentos_sdk.client import AgentOSClient
from agentos_sdk.langchain import AgentOSCallbackHandler

# 1. Initialize AgentOS Client
client = AgentOSClient(
    api_url="http://localhost:8000",
    api_key="demo-key",
    agent_id="langchain-demo-agent",
    agent_name="LangChain Demo Bot",
    version_id="v1.0"
)

# 2. Create the Callback Handler
agentos_cb = AgentOSCallbackHandler(client)

# 3. Setup LangChain Agent (using Fake LLM for demo)
llm = FakeListLLM(responses=["I can help with that.", "The answer is 42."])
tools = load_tools(["llm-math"], llm=llm)

agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True
)

# 4. Run the agent with the callback
print("Running agent...")
try:
    agent.run(
        "What is 2 + 2?", 
        callbacks=[agentos_cb]
    )
except Exception as e:
    print(f"Agent run failed (expected with fake tools): {e}")

# 5. Flush telemetry
print("Flushing telemetry...")
agentos_cb.flush()
print("Done! Check the AgentOS UI.")
