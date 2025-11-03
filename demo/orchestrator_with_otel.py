"""
Orchestrator Agent with OpenTelemetry for Jaeger
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

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Setup OpenTelemetry
resource = Resource(attributes={"service.name": "orchestrator-agent"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Export to Jaeger via OTLP HTTP endpoint
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:32073/v1/traces",
    insecure=True
)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = FastAPI(title="Orchestrator with OpenTelemetry")

AGENT_ID = "orchestrator-001"
ATP_INGEST_URL = os.getenv("ATP_INGEST_URL", "http://localhost:30001")
RESEARCH_AGENT_URL = "http://localhost:9001"
WRITER_AGENT_URL = "http://localhost:9002"
REVIEWER_AGENT_URL = "http://localhost:9003"

class TaskRequest(BaseModel):
    task: str
    trace_id: str = None

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "orchestrator", "telemetry": "opentelemetry"}

@app.post("/invoke")
async def invoke(request: TaskRequest):
    with tracer.start_as_current_span("orchestrator_workflow") as root_span:
        root_span.set_attribute("agent.id", AGENT_ID)
        root_span.set_attribute("task", request.task)
        
        # Planning span
        with tracer.start_as_current_span("planning") as plan_span:
            plan_span.set_attribute("model.provider", "openai")
            plan_span.set_attribute("model.name", "gpt-4o")
            plan_span.set_attribute("model.temperature", 0.3)
            
            await asyncio.sleep(0.15)
            plan_result = f"Plan: 1) Research 2) Write 3) Review"
            plan_span.set_attribute("output", plan_result)
        
        # Research agent call
        with tracer.start_as_current_span("call_research_agent") as research_span:
            research_span.set_attribute("kind", "subagent")
            research_span.set_attribute("remote.agent", "research-agent-001")
            research_span.set_attribute("remote.model", "claude-sonnet")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{RESEARCH_AGENT_URL}/invoke",
                        json={"query": request.task}
                    )
                    research_data = response.json()
                    research_span.set_attribute("status", "success")
            except Exception as e:
                research_data = {"result": f"Error: {e}"}
                research_span.set_attribute("status", "error")
                research_span.record_exception(e)
        
        # Writer agent call
        with tracer.start_as_current_span("call_writer_agent") as writer_span:
            writer_span.set_attribute("kind", "subagent")
            writer_span.set_attribute("remote.agent", "writer-agent-001")
            writer_span.set_attribute("remote.model", "gpt-4o-mini")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{WRITER_AGENT_URL}/invoke",
                        json={"content": research_data.get("result", "")}
                    )
                    writer_data = response.json()
                    writer_span.set_attribute("status", "success")
            except Exception as e:
                writer_data = {"result": f"Error: {e}"}
                writer_span.set_attribute("status", "error")
                writer_span.record_exception(e)
        
        # Reviewer agent call
        with tracer.start_as_current_span("call_reviewer_agent") as reviewer_span:
            reviewer_span.set_attribute("kind", "subagent")
            reviewer_span.set_attribute("remote.agent", "reviewer-agent-001")
            reviewer_span.set_attribute("remote.model", "gemini-pro")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{REVIEWER_AGENT_URL}/invoke",
                        json={"draft": writer_data.get("result", "")}
                    )
                    reviewer_data = response.json()
                    reviewer_span.set_attribute("status", "success")
            except Exception as e:
                reviewer_data = {"result": f"Error: {e}"}
                reviewer_span.set_attribute("status", "error")
                reviewer_span.record_exception(e)
        
        root_span.set_attribute("agents.called", 3)
        root_span.set_attribute("status", "success")
        
        return {
            "trace_id": format(root_span.get_span_context().trace_id, '032x'),
            "span_id": format(root_span.get_span_context().span_id, '016x'),
            "result": {
                "plan": plan_result,
                "research": research_data.get("result"),
                "draft": writer_data.get("result"),
                "review": reviewer_data.get("result")
            },
            "agents_called": 3,
            "telemetry": "opentelemetry_to_jaeger"
        }
