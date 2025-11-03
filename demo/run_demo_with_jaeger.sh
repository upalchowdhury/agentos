#!/bin/bash
# Multi-Agent Demo with Jaeger Tracing

set -e

echo "🚀 Starting Multi-Agent Demo with Jaeger Tracing"
echo "================================================="
echo ""

# Kill existing
pkill -f orchestrator_with_otel || true
pkill -f research_agent || true
pkill -f writer_agent || true
pkill -f reviewer_agent || true

sleep 2

cd "$(dirname "$0")"

echo "📦 Installing OpenTelemetry..."
pip3 install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc -q 2>/dev/null || echo "OpenTelemetry already installed"

echo ""
echo "🤖 Starting Agents with Jaeger instrumentation..."
echo ""

uvicorn research_agent:app --port 9001 > /tmp/research.log 2>&1 &
uvicorn writer_agent:app --port 9002 > /tmp/writer.log 2>&1 &
uvicorn reviewer_agent:app --port 9003 > /tmp/reviewer.log 2>&1 &
uvicorn orchestrator_with_otel:app --port 9000 > /tmp/orch_otel.log 2>&1 &

sleep 5

echo "✅ Agents running with OpenTelemetry!"
echo ""
echo "🧪 Running workflow..."
curl -X POST http://localhost:9000/invoke \
  -H "Content-Type: application/json" \
  -d '{"task": "AI innovations 2025"}' | jq

echo ""
echo "⏳ Waiting 5 seconds for traces to reach Jaeger..."
sleep 5

echo ""
echo "✅ TRACES SENT TO JAEGER!"
echo ""
echo "📊 View in Jaeger:"
echo "   1. Open: http://localhost:31686"
echo "   2. Service: 'orchestrator-agent'"
echo "   3. Click 'Find Traces'"
echo "   4. See hierarchical spans with:"
echo "      • orchestrator_workflow (root)"
echo "      • ├─ planning"
echo "      • ├─ call_research_agent"
echo "      • ├─ call_writer_agent"
echo "      • └─ call_reviewer_agent"
echo ""
echo "🎯 Each span shows:"
echo "   • Agent IDs"
echo "   • Model names (GPT-4o, Claude, GPT-4o-mini, Gemini)"
echo "   • Duration timeline"
echo "   • Status and tags"
