"""
Orchestrator Agent - Coordinates multiple agents
Uses GPT-4o for planning and coordination
"""
import asyncio
import hashlib
import json
import time
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Orchestrator Agent")

AGENT_ID = "orchestrator-001"
VERSION_ID = "v1.0.0"
ATP_INGEST_URL = os.getenv("ATP_INGEST_URL", "http://localhost:30001")

# Other agents
RESEARCH_AGENT_URL = "http://localhost:9001"
WRITER_AGENT_URL = "http://localhost:9002"
REVIEWER_AGENT_URL = "http://localhost:9003"

class TaskRequest(BaseModel):
    task: str
    trace_id: str = None

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def send_telemetry(trace_id: str, invocation_id: str, spans: list, edges: list):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{ATP_INGEST_URL}/v1/telemetry/spans",
                json={"trace_id": trace_id, "invocation_id": invocation_id, "spans": spans, "edges": edges}
            )
            await client.post(
                f"{ATP_INGEST_URL}/v1/telemetry/events",
                json={
                    "trace": {
                        "trace_id": trace_id,
                        "invocation_id": invocation_id,
                        "agent_id": AGENT_ID,
                        "protocol": "http",
                        "status": "success",
                        "start_ts": datetime.utcnow().isoformat() + "Z",
                        "end_ts": datetime.utcnow().isoformat() + "Z",
                        "execution_time_ms": 100,
                        "cost_cents": 20
                    },
                    "steps": []
                }
            )
    except Exception as e:
        print(f"Telemetry error: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "orchestrator", "model": "gpt-4o"}

@app.post("/invoke")
async def invoke(request: TaskRequest):
    trace_id = request.trace_id or str(uuid4())
    inv_id = str(uuid4())
    start = time.time()
    
    spans = []
    edges = []
    
    # Root span
    root_span_id = str(uuid4())
    root_start = start
    
    # Span 1: Planning (GPT-4o)
    plan_span_id = str(uuid4())
    plan_start = time.time()
    
    plan_prompt = f"Create a plan to: {request.task}"
    plan_hash = compute_hash(plan_prompt)
    await asyncio.sleep(0.15)  # Simulate GPT-4o call
    
    plan_result = f"Plan: 1) Research 2) Write 3) Review"
    plan_hash_out = compute_hash(plan_result)
    
    plan_end = time.time()
    spans.append({
        "span_id": plan_span_id,
        "parent_span_id": root_span_id,
        "name": "orchestrator_planning",
        "kind": "prompt",
        "start_ts": datetime.utcfromtimestamp(plan_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(plan_end).isoformat() + "Z",
        "duration_ms": int((plan_end - plan_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID},
        "model": {
            "provider": "openai",
            "name": "gpt-4o",
            "parameters": {"temperature": 0.3, "max_tokens": 500}
        },
        "io": {
            "tokens_in": 25,
            "tokens_out": 60,
            "input_excerpt": plan_prompt,
            "output_excerpt": plan_result,
            "content_hash_in": plan_hash,
            "content_hash_out": plan_hash_out
        }
    })
    
    # Span 2: Call Research Agent
    research_span_id = str(uuid4())
    research_start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            research_response = await client.post(
                f"{RESEARCH_AGENT_URL}/invoke",
                json={"query": request.task, "trace_id": trace_id}
            )
            research_data = research_response.json()
    except Exception as e:
        research_data = {"result": f"Error: {e}"}
    
    research_end = time.time()
    research_sub_span_id = research_data.get("span_id", str(uuid4()))
    
    spans.append({
        "span_id": research_span_id,
        "parent_span_id": root_span_id,
        "name": "call_research_agent",
        "kind": "subagent",
        "start_ts": datetime.utcfromtimestamp(research_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(research_end).isoformat() + "Z",
        "duration_ms": int((research_end - research_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID},
        "network": {
            "protocol": "http",
            "remote_agent_id": "research-agent-001",
            "edge_id": str(uuid4())
        }
    })
    
    # Edge: Orchestrator -> Research Agent
    edge_id_research = str(uuid4())
    edges.append({
        "edge_id": edge_id_research,
        "time": datetime.utcfromtimestamp(research_start).isoformat() + "Z",
        "from_agent_id": AGENT_ID,
        "from_version_id": VERSION_ID,
        "from_span_id": research_span_id,
        "to_agent_id": "research-agent-001",
        "to_span_id": research_sub_span_id,
        "channel": "http",
        "instruction_type": "tool_request",
        "size_bytes": len(json.dumps({"query": request.task})),
        "signature_verified": False,
        "content_hash": compute_hash(request.task)
    })
    
    # Span 3: Call Writer Agent
    writer_span_id = str(uuid4())
    writer_start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            writer_response = await client.post(
                f"{WRITER_AGENT_URL}/invoke",
                json={"content": research_data.get("result", ""), "trace_id": trace_id}
            )
            writer_data = writer_response.json()
    except Exception as e:
        writer_data = {"result": f"Error: {e}"}
    
    writer_end = time.time()
    writer_sub_span_id = writer_data.get("span_id", str(uuid4()))
    
    spans.append({
        "span_id": writer_span_id,
        "parent_span_id": root_span_id,
        "name": "call_writer_agent",
        "kind": "subagent",
        "start_ts": datetime.utcfromtimestamp(writer_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(writer_end).isoformat() + "Z",
        "duration_ms": int((writer_end - writer_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID},
        "network": {
            "protocol": "http",
            "remote_agent_id": "writer-agent-001",
            "edge_id": str(uuid4())
        }
    })
    
    # Edge: Orchestrator -> Writer Agent
    edge_id_writer = str(uuid4())
    edges.append({
        "edge_id": edge_id_writer,
        "time": datetime.utcfromtimestamp(writer_start).isoformat() + "Z",
        "from_agent_id": AGENT_ID,
        "from_span_id": writer_span_id,
        "to_agent_id": "writer-agent-001",
        "to_span_id": writer_sub_span_id,
        "channel": "http",
        "instruction_type": "prompt",
        "size_bytes": len(json.dumps({"content": research_data.get("result", "")})),
        "signature_verified": False
    })
    
    # Span 4: Call Reviewer Agent
    reviewer_span_id = str(uuid4())
    reviewer_start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            reviewer_response = await client.post(
                f"{REVIEWER_AGENT_URL}/invoke",
                json={"draft": writer_data.get("result", ""), "trace_id": trace_id}
            )
            reviewer_data = reviewer_response.json()
    except Exception as e:
        reviewer_data = {"result": f"Error: {e}"}
    
    reviewer_end = time.time()
    reviewer_sub_span_id = reviewer_data.get("span_id", str(uuid4()))
    
    spans.append({
        "span_id": reviewer_span_id,
        "parent_span_id": root_span_id,
        "name": "call_reviewer_agent",
        "kind": "subagent",
        "start_ts": datetime.utcfromtimestamp(reviewer_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(reviewer_end).isoformat() + "Z",
        "duration_ms": int((reviewer_end - reviewer_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID},
        "network": {
            "protocol": "http",
            "remote_agent_id": "reviewer-agent-001",
            "edge_id": str(uuid4())
        }
    })
    
    # Edge: Orchestrator -> Reviewer Agent
    edge_id_reviewer = str(uuid4())
    edges.append({
        "edge_id": edge_id_reviewer,
        "time": datetime.utcfromtimestamp(reviewer_start).isoformat() + "Z",
        "from_agent_id": AGENT_ID,
        "from_span_id": reviewer_span_id,
        "to_agent_id": "reviewer-agent-001",
        "to_span_id": reviewer_sub_span_id,
        "channel": "http",
        "instruction_type": "system_directive",
        "size_bytes": len(json.dumps({"draft": writer_data.get("result", "")})),
        "signature_verified": False
    })
    
    end = time.time()
    
    # Root span
    spans.insert(0, {
        "span_id": root_span_id,
        "parent_span_id": None,
        "name": "orchestrator_workflow",
        "kind": "system",
        "start_ts": datetime.utcfromtimestamp(root_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(end).isoformat() + "Z",
        "duration_ms": int((end - root_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID}
    })
    
    # Send telemetry
    await send_telemetry(trace_id, inv_id, spans, edges)
    
    return {
        "trace_id": trace_id,
        "invocation_id": inv_id,
        "span_id": root_span_id,
        "result": {
            "plan": plan_result,
            "research": research_data.get("result"),
            "draft": writer_data.get("result"),
            "review": reviewer_data.get("result")
        },
        "agents_called": 3,
        "edges_created": 3
    }
