"""
Reviewer Agent - Uses Gemini for quality review
"""
import asyncio
import hashlib
import time
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Reviewer Agent")

AGENT_ID = "reviewer-agent-001"
VERSION_ID = "v1.0.0"
ATP_INGEST_URL = os.getenv("ATP_INGEST_URL", "http://localhost:30001")

class ReviewRequest(BaseModel):
    draft: str
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
                        "execution_time_ms": 90,
                        "cost_cents": 4
                    },
                    "steps": []
                }
            )
    except Exception as e:
        print(f"Telemetry error: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "reviewer", "model": "gemini-pro"}

@app.post("/invoke")
async def invoke(request: ReviewRequest):
    trace_id = request.trace_id or str(uuid4())
    inv_id = str(uuid4())
    start = time.time()
    
    spans = []
    root_span_id = str(uuid4())
    
    # Review span with Gemini
    review_span_id = str(uuid4())
    review_start = time.time()
    
    prompt = f"Review this draft: {request.draft}"
    prompt_hash = compute_hash(prompt)
    await asyncio.sleep(0.11)  # Simulate Gemini API call
    
    result = "Review: Excellent quality, well-structured content. Minor suggestions: add more examples, strengthen conclusion. Overall: Approved."
    result_hash = compute_hash(result)
    
    review_end = time.time()
    
    spans.append({
        "span_id": review_span_id,
        "parent_span_id": root_span_id,
        "name": "gemini_review",
        "kind": "prompt",
        "start_ts": datetime.utcfromtimestamp(review_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(review_end).isoformat() + "Z",
        "duration_ms": int((review_end - review_start) * 1000),
        "status": "success",
        "agent": {"agent_id": AGENT_ID, "version_id": VERSION_ID},
        "model": {
            "provider": "google",
            "name": "gemini-1.5-pro",
            "parameters": {"temperature": 0.2, "max_tokens": 600}
        },
        "io": {
            "tokens_in": 50,
            "tokens_out": 120,
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
        "name": "review_task",
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
