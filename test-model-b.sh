#!/bin/bash
# Test Model B Agent Registration and Invocation

set -e

RUNTIME_URL="http://localhost:30000"
INGEST_URL="http://localhost:30001"
OBS_URL="http://localhost:30003"
AGENT_URL="http://localhost:9000"

command=$1
agent_id=$2

case $command in
  "register")
    echo "📝 Registering Model B test agent..."
    
    response=$(curl -s -X POST "$RUNTIME_URL/v1/agents/modelB" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "model-b-test-agent",
        "endpoint_url": "'"$AGENT_URL"'",
        "auth_config": {
          "type": "none"
        },
        "rate_limit_config": {
          "rps": 10,
          "burst": 20
        },
        "metadata": {
          "description": "Test agent for Model B deployment",
          "protocol": "http"
        }
      }')
    
    echo "$response" | jq .
    
    agent_id=$(echo "$response" | jq -r '.agent_id')
    
    if [ "$agent_id" != "null" ] && [ -n "$agent_id" ]; then
      echo ""
      echo "✅ Agent registered successfully!"
      echo "Agent ID: $agent_id"
      echo ""
      echo "Save this agent_id for invocation:"
      echo "  export AGENT_ID='$agent_id'"
      echo ""
      echo "Or invoke directly:"
      echo "  ./test-model-b.sh invoke $agent_id"
    else
      echo "❌ Registration failed"
      exit 1
    fi
    ;;
    
  "invoke")
    if [ -z "$agent_id" ]; then
      echo "Usage: ./test-model-b.sh invoke <agent-id>"
      exit 1
    fi
    
    echo "🚀 Invoking agent: $agent_id"
    echo ""
    
    # Direct invocation to external agent
    response=$(curl -s -X POST "$AGENT_URL/invoke" \
      -H "Content-Type: application/json" \
      -d '{
        "input": {
          "message": "Hello from Kubernetes!",
          "test_data": {
            "value": 42,
            "timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
          }
        }
      }')
    
    echo "Response:"
    echo "$response" | jq .
    
    trace_id=$(echo "$response" | jq -r '.trace_id')
    invocation_id=$(echo "$response" | jq -r '.invocation_id')
    
    echo ""
    echo "✅ Invocation completed!"
    echo "Trace ID: $trace_id"
    echo "Invocation ID: $invocation_id"
    
    # Wait for telemetry to be processed
    echo ""
    echo "⏳ Waiting for telemetry processing (3 seconds)..."
    sleep 3
    
    # Try to fetch trace
    echo ""
    echo "📊 Fetching trace from Observability API..."
    trace_response=$(curl -s "$OBS_URL/v1/traces/$trace_id")
    
    if echo "$trace_response" | jq -e '.trace_id' > /dev/null 2>&1; then
      echo "$trace_response" | jq .
      echo ""
      echo "✅ Trace retrieved successfully!"
    else
      echo "⚠️  Trace not yet available (may need more time)"
      echo "Response: $trace_response"
    fi
    ;;
    
  "list-agents")
    echo "📋 Listing all agents..."
    curl -s "$RUNTIME_URL/v1/catalog/agents" | jq .
    ;;
    
  "view-trace")
    if [ -z "$agent_id" ]; then
      echo "Usage: ./test-model-b.sh view-trace <trace-id>"
      exit 1
    fi
    
    trace_id=$agent_id  # Reusing parameter
    echo "📊 Fetching trace: $trace_id"
    curl -s "$OBS_URL/v1/traces/$trace_id" | jq .
    ;;
    
  "list-traces")
    echo "📋 Listing recent traces..."
    curl -s "$OBS_URL/v1/traces?limit=10" | jq .
    ;;
    
  "agent-metrics")
    if [ -z "$agent_id" ]; then
      echo "Usage: ./test-model-b.sh agent-metrics <agent-id>"
      exit 1
    fi
    
    echo "📈 Fetching metrics for agent: $agent_id"
    curl -s "$OBS_URL/v1/agents/$agent_id/metrics" | jq .
    ;;
    
  "cost-summary")
    echo "💰 Fetching cost summary..."
    curl -s "$RUNTIME_URL/v1/cost/summary?period_days=7" | jq .
    ;;
    
  "catalog")
    echo "🏪 Browsing agent catalog..."
    curl -s "$RUNTIME_URL/v1/catalog/agents?sort_by=popularity&limit=20" | jq .
    ;;
    
  "health")
    echo "🏥 Checking service health..."
    echo ""
    echo "Runtime:"
    curl -s "$RUNTIME_URL/health" | jq .
    echo ""
    echo "Ingest:"
    curl -s "$INGEST_URL/health" | jq .
    echo ""
    echo "Observability:"
    curl -s "$OBS_URL/health" | jq .
    echo ""
    echo "Test Agent:"
    curl -s "$AGENT_URL/health" | jq . || echo "⚠️  Test agent not running"
    ;;
    
  *)
    echo "AgentOS Model B Test Script"
    echo ""
    echo "Usage: ./test-model-b.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  register              Register the Model B test agent"
    echo "  invoke <agent-id>     Invoke the agent and view telemetry"
    echo "  list-agents           List all registered agents"
    echo "  view-trace <trace-id> View a specific trace"
    echo "  list-traces           List recent traces"
    echo "  agent-metrics <id>    View agent metrics"
    echo "  cost-summary          View cost summary"
    echo "  catalog               Browse agent catalog"
    echo "  health                Check all services health"
    echo ""
    echo "Example workflow:"
    echo "  1. ./test-model-b.sh register"
    echo "  2. ./test-model-b.sh invoke <agent-id-from-step-1>"
    echo "  3. ./test-model-b.sh agent-metrics <agent-id>"
    ;;
esac
