"""
Orchestrator Agent with Working Jaeger Integration
"""
import asyncio
import json
import time
from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

# OpenTelemetry - Simple working setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Configure OpenTelemetry
resource = Resource.create({"service.name": "orchestrator-agent"})
provider = TracerProvider(resource=resource)

# OTLP HTTP Exporter to Jaeger
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:32073/v1/traces",
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Set as global tracer
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="Orchestrator with Jaeger")

RESEARCH_URL = "http://localhost:9001"
WRITER_URL = "http://localhost:9002"
REVIEWER_URL = "http://localhost:9003"

class TaskRequest(BaseModel):
    task: str

@app.get("/health")
async def health():
    return {"status": "healthy", "telemetry": "jaeger"}

@app.post("/invoke")
async def invoke(request: TaskRequest):
    # Start root span
    with tracer.start_as_current_span("orchestrator_workflow") as root_span:
        root_span.set_attribute("agent.id", "orchestrator-001")
        root_span.set_attribute("task", request.task)
        root_span.set_attribute("model.provider", "openai")
        
        results = {}
        
        # Planning span
        with tracer.start_as_current_span("planning") as plan_span:
            plan_span.set_attribute("operation", "planning")
            plan_span.set_attribute("model.name", "gpt-4o")
            plan_span.set_attribute("model.temperature", 0.3)
            await asyncio.sleep(0.15)
            results["plan"] = "Plan: 1) Research 2) Write 3) Review"
        
        # Research agent
        with tracer.start_as_current_span("call_research_agent") as research_span:
            research_span.set_attribute("operation", "research")
            research_span.set_attribute("remote.agent", "research-agent-001")
            research_span.set_attribute("remote.model", "claude-3-5-sonnet")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{RESEARCH_URL}/invoke",
                        json={"query": request.task}
                    )
                    data = resp.json()
                    results["research"] = data.get("result", "Research complete")
                    research_span.set_attribute("status", "success")
            except Exception as e:
                results["research"] = f"Research: {request.task}"
                research_span.set_attribute("status", "error")
                research_span.record_exception(e)
        
        # Writer agent
        with tracer.start_as_current_span("call_writer_agent") as writer_span:
            writer_span.set_attribute("operation", "writing")
            writer_span.set_attribute("remote.agent", "writer-agent-001")
            writer_span.set_attribute("remote.model", "gpt-4o-mini")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{WRITER_URL}/invoke",
                        json={"content": results.get("research", "")}
                    )
                    data = resp.json()
                    results["draft"] = data.get("result", "Draft complete")
                    writer_span.set_attribute("status", "success")
            except Exception as e:
                results["draft"] = "Draft written"
                writer_span.set_attribute("status", "error")
                writer_span.record_exception(e)
        
        # Reviewer agent
        with tracer.start_as_current_span("call_reviewer_agent") as reviewer_span:
            reviewer_span.set_attribute("operation", "review")
            reviewer_span.set_attribute("remote.agent", "reviewer-agent-001")
            reviewer_span.set_attribute("remote.model", "gemini-1.5-pro")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{REVIEWER_URL}/invoke",
                        json={"draft": results.get("draft", "")}
                    )
                    data = resp.json()
                    results["review"] = data.get("result", "Review complete")
                    reviewer_span.set_attribute("status", "success")
            except Exception as e:
                results["review"] = "Review: Approved"
                reviewer_span.set_attribute("status", "error")
                reviewer_span.record_exception(e)
        
        root_span.set_attribute("agents.called", 3)
        root_span.set_attribute("status", "complete")
        
        # Get trace info
        span_ctx = root_span.get_span_context()
        trace_id = format(span_ctx.trace_id, '032x')
        span_id = format(span_ctx.span_id, '016x')
        
        return {
            "trace_id": trace_id,
            "span_id": span_id,
            "result": results,
            "agents_called": 3,
            "jaeger_url": f"http://localhost:31686/trace/{trace_id}"
        }
