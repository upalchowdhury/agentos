#!/usr/bin/env python3
"""
Simple test to send a trace directly to Jaeger
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import time

# Setup
resource = Resource(attributes={"service.name": "test-trace-service"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Try console first to verify spans work
console_exporter = ConsoleSpanExporter()
provider.add_span_processor(BatchSpanProcessor(console_exporter))

# Also try Jaeger
try:
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:32073/v1/traces",
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    print("✅ OTLP exporter configured")
except Exception as e:
    print(f"⚠️  OTLP exporter failed: {e}")

# Create a trace
tracer = trace.get_tracer(__name__)

print("\n🔵 Creating test trace...")
with tracer.start_as_current_span("test-root-span") as root:
    root.set_attribute("test.attribute", "test-value")
    root.set_attribute("agent.id", "test-agent-001")
    
    time.sleep(0.1)
    
    with tracer.start_as_current_span("child-span-1") as child1:
        child1.set_attribute("operation", "research")
        child1.set_attribute("model", "claude-sonnet")
        time.sleep(0.05)
    
    with tracer.start_as_current_span("child-span-2") as child2:
        child2.set_attribute("operation", "write")
        child2.set_attribute("model", "gpt-4o-mini")
        time.sleep(0.05)

print("✅ Trace created")
print("⏳ Flushing to exporters...")
time.sleep(2)

print("\n📊 Check Jaeger UI:")
print("   http://localhost:31686")
print("   Service: 'test-trace-service'")
