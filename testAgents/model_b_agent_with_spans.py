"""Model B Test Agent with ATP v0.1 Span-Level Telemetry"""
import json
import time
import os
import hashlib
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI(title="Model B Test Agent with Spans")

class InvokeRequest(BaseModel):
    input: dict
    trace_id: str = None

class InvokeResponse(BaseModel):
    output: dict
    trace_id: str
    invocation_id: str
    execution_time_ms: int

ATP_INGEST_URL = os.getenv("ATP_INGEST_URL", "http://ingest:8001")
AGENT_ID = "550e8400-e29b-41d4-a716-446655440000"
VERSION_ID = "v1.0.0-spans"

def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]

async def send_span_telemetry(trace_id: str, invocation_id: str, spans: list, edges: list = None):
    """Send span-level telemetry to ATP ingest"""
    try:
        payload = {
            "trace_id": trace_id,
            "invocation_id": invocation_id,
            "spans": spans,
            "edges": edges or []
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{ATP_INGEST_URL}/v1/telemetry/spans",
                json=payload
            )
            response.raise_for_status()
            print(f"✅ Sent {len(spans)} spans to ATP ingest")
    except Exception as e:
        print(f"❌ Telemetry failed: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "model-b-spans", "version": VERSION_ID}

@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest):
    trace_id = request.trace_id or str(uuid4())
    inv_id = str(uuid4())
    overall_start = time.time()
    
    spans = []
    
    # Root span - invocation
    root_span_id = str(uuid4())
    root_start = overall_start
    
    # Span 1: Input processing
    input_span_id = str(uuid4())
    input_start = time.time()
    
    # Simulate input processing
    input_text = json.dumps(request.input)
    input_hash = compute_hash(input_text)
    time.sleep(0.05)
    
    input_end = time.time()
    spans.append({
        "span_id": input_span_id,
        "parent_span_id": root_span_id,
        "name": "input_processing",
        "kind": "system",
        "start_ts": datetime.utcfromtimestamp(input_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(input_end).isoformat() + "Z",
        "duration_ms": int((input_end - input_start) * 1000),
        "status": "success",
        "agent": {
            "agent_id": AGENT_ID,
            "version_id": VERSION_ID
        },
        "io": {
            "input_excerpt": input_text[:100],
            "content_hash_in": input_hash,
            "signature_verified": False
        }
    })
    
    # Span 2: Model inference (simulated)
    model_span_id = str(uuid4())
    model_start = time.time()
    
    # Simulate model call
    prompt = f"Process: {request.input}"
    prompt_hash = compute_hash(prompt)
    time.sleep(0.1)  # Simulate inference
    
    response_text = f"Processed: {request.input}"
    response_hash = compute_hash(response_text)
    
    model_end = time.time()
    spans.append({
        "span_id": model_span_id,
        "parent_span_id": root_span_id,
        "name": "model_inference",
        "kind": "prompt",
        "start_ts": datetime.utcfromtimestamp(model_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(model_end).isoformat() + "Z",
        "duration_ms": int((model_end - model_start) * 1000),
        "status": "success",
        "agent": {
            "agent_id": AGENT_ID,
            "version_id": VERSION_ID
        },
        "model": {
            "provider": "openai",
            "name": "gpt-4o-mini",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 150,
                "seed": 42
            }
        },
        "io": {
            "tokens_in": len(prompt.split()),
            "tokens_out": len(response_text.split()),
            "input_excerpt": prompt[:200],
            "output_excerpt": response_text[:200],
            "content_hash_in": prompt_hash,
            "content_hash_out": response_hash,
            "signature_verified": False
        }
    })
    
    # Span 3: Tool call (simulated)
    tool_span_id = str(uuid4())
    tool_start = time.time()
    
    # Simulate tool execution
    tool_args = {"action": "process", "data": request.input}
    tool_result = {"status": "success", "timestamp": datetime.utcnow().isoformat()}
    time.sleep(0.05)
    
    tool_end = time.time()
    spans.append({
        "span_id": tool_span_id,
        "parent_span_id": root_span_id,
        "name": "process_tool",
        "kind": "tool",
        "start_ts": datetime.utcfromtimestamp(tool_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(tool_end).isoformat() + "Z",
        "duration_ms": int((tool_end - tool_start) * 1000),
        "status": "success",
        "agent": {
            "agent_id": AGENT_ID,
            "version_id": VERSION_ID
        },
        "tool": {
            "call_id": str(uuid4()),
            "name": "process_data",
            "args_excerpt": json.dumps(tool_args)[:200],
            "return_excerpt": json.dumps(tool_result)[:200]
        }
    })
    
    overall_end = time.time()
    
    # Root span
    spans.insert(0, {
        "span_id": root_span_id,
        "parent_span_id": None,
        "name": "agent_invocation",
        "kind": "system",
        "start_ts": datetime.utcfromtimestamp(root_start).isoformat() + "Z",
        "end_ts": datetime.utcfromtimestamp(overall_end).isoformat() + "Z",
        "duration_ms": int((overall_end - root_start) * 1000),
        "status": "success",
        "agent": {
            "agent_id": AGENT_ID,
            "version_id": VERSION_ID
        }
    })
    
    output = {
        "result": "success",
        "message": response_text,
        "timestamp": datetime.utcnow().isoformat(),
        "spans_generated": len(spans)
    }
    
    # Send spans to ATP ingest
    await send_span_telemetry(trace_id, inv_id, spans)
    
    # Also send legacy event format for backward compatibility
    await send_legacy_telemetry(trace_id, inv_id, overall_start, overall_end)
    
    return InvokeResponse(
        output=output,
        trace_id=trace_id,
        invocation_id=inv_id,
        execution_time_ms=int((overall_end - overall_start) * 1000)
    )

async def send_legacy_telemetry(trace_id: str, inv_id: str, start: float, end: float):
    """Send legacy ATP v0 telemetry for backward compatibility"""
    try:
        exec_ms = int((end - start) * 1000)
        payload = {
            "trace": {
                "trace_id": trace_id,
                "invocation_id": inv_id,
                "agent_id": AGENT_ID,
                "protocol": "http",
                "status": "success",
                "start_ts": datetime.utcfromtimestamp(start).isoformat() + "Z",
                "end_ts": datetime.utcfromtimestamp(end).isoformat() + "Z",
                "execution_time_ms": exec_ms,
                "cost_cents": 5
            },
            "steps": []
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{ATP_INGEST_URL}/v1/telemetry/events", json=payload)
    except Exception as e:
        print(f"Legacy telemetry failed: {e}")
