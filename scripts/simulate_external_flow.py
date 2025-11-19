import requests
import time
import uuid
import json
from datetime import datetime, timezone

# Configuration
API_URL = "http://localhost:8000/v1"  # Assuming local ingest service
# For demo purposes, we might print to console if API isn't running, 
# but let's assume we want to generate data structure for the UI to consume.

def generate_trace_id():
    return str(uuid.uuid4()).replace('-', '')

def generate_span_id():
    return str(uuid.uuid4()).replace('-', '')[:16]

def current_time():
    return datetime.now(timezone.utc).isoformat()

def simulate_flow():
    trace_id = generate_trace_id()
    
    # 1. Salesforce Agent (External) receives user query
    sf_span_id = generate_span_id()
    sf_event = {
        "id": str(uuid.uuid4()),
        "platform": "salesforce_agentforce",
        "tenantId": "org_default",
        "timestamp": current_time(),
        "agent": {
            "id": "agent_salesforce_01",
            "name": "Salesforce Service Bot",
            "version": "v1.2",
            "type": "conversational"
        },
        "execution": {
            "traceId": trace_id,
            "spanId": sf_span_id,
            "durationMs": 1200,
            "status": "success"
        },
        "io": {
            "input": "Customer asking for refund status on order #12345",
            "output": "Checking order status...",
            "piiDetected": False
        }
    }
    
    # 2. Salesforce Agent calls GCP Research Agent (Cross-Platform Edge)
    # This represents an HTTP call or similar
    
    # 3. GCP Agent (External) processes request
    gcp_span_id = generate_span_id()
    gcp_event = {
        "id": str(uuid.uuid4()),
        "platform": "gcp_agent_engine",
        "tenantId": "org_default",
        "timestamp": current_time(),
        "agent": {
            "id": "agent_gcp_research",
            "name": "GCP Research Assistant",
            "version": "v2.0",
            "type": "analytical"
        },
        "execution": {
            "traceId": trace_id,
            "spanId": gcp_span_id,
            "parentSpanId": sf_span_id, # Linked to Salesforce agent
            "durationMs": 800,
            "status": "success"
        },
        "llm": {
            "provider": "vertex_ai",
            "model": "gemini-pro",
            "inputTokens": 150,
            "outputTokens": 50,
            "totalCostUsd": 0.002
        },
        "io": {
            "input": "Check refund policy for order #12345",
            "output": "Refund approved. Policy allows 30-day returns.",
            "piiDetected": False
        }
    }

    # 4. Policy Violation Simulation (Attempted PII Access)
    violation_span_id = generate_span_id()
    violation_event = {
        "id": str(uuid.uuid4()),
        "platform": "gcp_agent_engine",
        "tenantId": "org_default",
        "timestamp": current_time(),
        "agent": {
            "id": "agent_gcp_research",
            "name": "GCP Research Assistant",
            "version": "v2.0",
            "type": "analytical"
        },
        "execution": {
            "traceId": trace_id,
            "spanId": violation_span_id,
            "parentSpanId": gcp_span_id,
            "durationMs": 100,
            "status": "failure"
        },
        "io": {
            "input": "Get customer credit card details for refund",
            "output": "[BLOCKED] Policy Violation: PII Access Denied",
            "piiDetected": True,
            "piiTypes": ["credit_card"]
        }
    }

    print(json.dumps([sf_event, gcp_event, violation_event], indent=2))

if __name__ == "__main__":
    simulate_flow()
