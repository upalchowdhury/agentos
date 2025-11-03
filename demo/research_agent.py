"""
Research Agent - Uses Claude Sonnet for research
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

app = FastAPI(title="Research Agent")

AGENT_ID = "research-agent-001"
VERSION_ID = "v1.0.0"
ATP_INGEST_URL = os.getenv("ATP_INGEST_URL", "http://localhost:30001")

class ResearchRequest(BaseModel):
    query: str
    trace_id: str = None

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def send_telemetry(trace_id: str, invocation_id: str, spans: list):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{ATP_INGEST_URL}/v1/telemetry/spans",
                json={"trace_id": trace_id, "invocation_id": invocation_id, "spans": spans, "edges": []}
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
                        "cost_cents": 8
                    },
                    "steps": []
                }
            )
    except Exception as e:
        print(f"Telemetry error: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "research", "model": "claude-sonnet"}

@app.post("/invoke")
async def invoke(request: ResearchRequest):
    trace_id = request.trace_id or str(uuid4())
    inv_id = str(uuid4())
    start = time.time()
    
    spans = []
    root_span_id = str(uuid4())
    
    # Research span with Claude
    research_span_id = str(uuid4())
    research_start = time.time()
    
    prompt = f"Research: {request.query}"
    prompt_hash = compute_hash(prompt)
    await asyncio.sleep(0.12)  # Simulate Claude API call
    
    result = f"Research findings on '{request.query}': Key insights include technological advances, market trends, and future implications."
    result_hash = compute_hash(result)
    
    research_end = time.time()
    
    spans.append({
        "span_id": research_span_id,
        "parent_span_id": root_span_id,
        "name": "claude_research",
        "kind": "prompt",
        "start_ts": datetime.utcfromtimestamp(research_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(research_end).isoformat() + "Z",
        "duration_ms": int((research_end - research_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID},
        "model": {
            "provider": "anthropic",
            "name": "claude-3-5-sonnet-20241022",
            "parameters": {"temperature": 0.5, "max_tokens": 1000}
        },
        "io": {
            "tokens_in": 35,
            "tokens_out": 180,
            "input_excerpt": prompt[:200],
            "output_excerpt": result[:200],
            "content_hash_in": prompt_hash,
            "content_hash_out": result_hash
        }
    })
    
    end = time.time()
    
    # Root span
    spans.insert(0, {
        "span_id": root_span_id,
        "parent_span_id": None,
        "name": "research_task",
        "kind": "system",
        "start_ts": datetime.utcfromtimestamp(start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(end).isoformat() + "Z",
        "duration_ms": int((end - start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID}
    })
    
    await send_telemetry(trace_id, inv_id, spans)
    
    return {
        "trace_id": trace_id,
        "invocation_id": inv_id,
        "span_id": root_span_id,
        "result": result
    }
