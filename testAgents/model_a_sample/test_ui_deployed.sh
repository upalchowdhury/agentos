#!/bin/bash
# Quick test script for UI-deployed agent
# Usage: ./test_ui_deployed.sh <agent-id>

AGENT_ID="${1}"
JWT_TOKEN="eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Ijp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA"

if [ -z "$AGENT_ID" ]; then
  echo "❌ Please provide agent ID"
  echo "Usage: $0 <agent-id>"
  exit 1
fi

echo "🧮 Testing Calculator Agent: $AGENT_ID"
echo ""

# Test 1: Addition
echo "Test 1: Addition [10, 20, 30]"
curl -s -X POST "http://localhost:8082/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "add",
      "numbers": [10, 20, 30]
    }
  }' | jq '{status, result: .result.result, cost}'

echo ""

# Test 2: Multiplication
echo "Test 2: Multiplication [5, 3, 2]"
curl -s -X POST "http://localhost:8082/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "multiply",
      "numbers": [5, 3, 2]
    }
  }' | jq '{status, result: .result.result, cost}'

echo ""

# Test 3: Average
echo "Test 3: Average [100, 200, 300]"
curl -s -X POST "http://localhost:8082/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "average",
      "numbers": [100, 200, 300]
    }
  }' | jq '{status, result: .result.result, cost}'

echo ""
echo "================================================"
echo "✅ Tests complete!"
echo "View in UI: http://localhost:3001/invocations"
echo ""
