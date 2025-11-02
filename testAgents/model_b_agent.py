"""Model B Test Agent with ATP v0 Telemetry"""
import json
import time
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI(title="Model B Test Agent")

class InvokeRequest(BaseModel):
    input: dict
    trace_id: str = None

class InvokeResponse(BaseModel):
    output: dict
    trace_id: str
    invocation_id: str
    execution_time_ms: int

ATP_INGEST_URL = "http://localhost:30001"

async def send_telemetry(trace_data: dict):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{ATP_INGEST_URL}/v1/telemetry/events", json=trace_data)
    except Exception as e:
        print(f"Telemetry failed: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "model-b-test"}

@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest):
    start = time.time()
    trace_id = request.trace_id or str(uuid4())
    inv_id = str(uuid4())
    
    # Simulate work
    time.sleep(0.2)
    
    end = time.time()
    exec_ms = int((end - start) * 1000)
    
    output = {
        "result": "success",
        "message": f"Processed: {request.input}",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send ATP telemetry (using UUID of registered agent)
    await send_telemetry({
        "trace": {
            "trace_id": trace_id,
            "invocation_id": inv_id,
            "agent_id": "550e8400-e29b-41d4-a716-446655440000",  # UUID of model-b-test-agent
            "protocol": "http",
            "status": "success",
            "start_ts": datetime.utcfromtimestamp(start).isoformat() + "Z",
            "end_ts": datetime.utcfromtimestamp(end).isoformat() + "Z",
            "execution_time_ms": exec_ms,
            "cost_cents": 5
        },
        "steps": [{
            "step_id": str(uuid4()),
            "name": "process",
            "kind": "tool",
            "start_ts": datetime.utcfromtimestamp(start).isoformat() + "Z",
            "end_ts": datetime.utcfromtimestamp(end).isoformat() + "Z",
            "latency_ms": exec_ms,
            "status": "success"
        }]
    })
    
    return InvokeResponse(
        output=output,
        trace_id=trace_id,
        invocation_id=inv_id,
        execution_time_ms=exec_ms
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
