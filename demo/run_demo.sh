#!/bin/bash
# Multi-Agent Demo Runner

export ATP_INGEST_URL="http://localhost:30001"

pkill -f orchestrator_agent || true
pkill -f research_agent || true
pkill -f writer_agent || true
pkill -f reviewer_agent || true

sleep 2

cd "$(dirname "$0")"

echo "🚀 Starting Multi-Agent Demo with 4 LLMs"
echo ""

uvicorn research_agent:app --port 9001 > /tmp/research.log 2>&1 &
uvicorn writer_agent:app --port 9002 > /tmp/writer.log 2>&1 &
uvicorn reviewer_agent:app --port 9003 > /tmp/reviewer.log 2>&1 &
uvicorn orchestrator_agent:app --port 9000 > /tmp/orch.log 2>&1 &

sleep 5

echo "✅ Agents running:"
echo "  • Orchestrator (GPT-4o) :9000"
echo "  • Research (Claude) :9001"
echo "  • Writer (GPT-4o-mini) :9002"
echo "  • Reviewer (Gemini) :9003"
echo ""
echo "🧪 Running demo workflow..."
curl -X POST http://localhost:9000/invoke \
  -H "Content-Type: application/json" \
  -d '{"task": "AI trends in 2025"}' | jq

echo ""
echo "📊 View in dashboard: http://localhost:30080"
echo "   Wait 10 seconds then refresh to see all agents!"
