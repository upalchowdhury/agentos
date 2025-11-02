#!/bin/bash
# Invoke Model A Agent

# Set your JWT token
JWT_TOKEN="eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Ijp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA"

RUNTIME_URL="http://localhost:8082"

# Get agent ID from argument or use default
AGENT_ID="${1:-YOUR_AGENT_ID_HERE}"

if [ "$AGENT_ID" = "YOUR_AGENT_ID_HERE" ]; then
  echo "❌ Please provide agent ID as argument"
  echo "Usage: $0 <agent_id>"
  exit 1
fi

echo "🧮 Invoking Calculator Agent: $AGENT_ID"
echo ""

# Example 1: Addition
echo "Example 1: Adding numbers [10, 20, 30, 40]"
curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "add",
      "numbers": [10, 20, 30, 40]
    }
  }' | jq '{status, result: .result.result, execution_time_ms, cost}'

echo ""
echo "================================================"
echo ""

# Example 2: Multiplication
echo "Example 2: Multiplying numbers [5, 3, 2]"
curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "multiply",
      "numbers": [5, 3, 2]
    }
  }' | jq '{status, result: .result.result, execution_time_ms, cost}'

echo ""
echo "================================================"
echo ""

# Example 3: Average
echo "Example 3: Averaging numbers [100, 200, 300]"
curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "operation": "average",
      "numbers": [100, 200, 300]
    }
  }' | jq '{status, result: .result.result, execution_time_ms, cost}'

echo ""
echo "================================================"
echo ""
echo "✅ Invocations complete!"
echo "View invocations in UI: http://localhost:3001/invocations"
echo ""
