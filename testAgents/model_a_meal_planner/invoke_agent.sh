#!/bin/bash
# Invoke Meal Planner Agent (Model A)

JWT_TOKEN="eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Injp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA"

RUNTIME_URL="http://localhost:8082"

AGENT_ID="${1:-YOUR_AGENT_ID}"

if [ "$AGENT_ID" = "YOUR_AGENT_ID" ]; then
  echo "❌ Please provide agent ID"
  echo "Usage: $0 <agent_id>"
  exit 1
fi

echo "🍽️  Testing Meal Planner Agent: $AGENT_ID"
echo ""

# Example 1: Quick breakfast
echo "Example 1: Quick breakfast idea"
curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "prompt": "Suggest a quick healthy breakfast for one person"
    }
  }' | jq '{status, response: .result.response[:200], execution_time_ms, cost}'

echo ""
echo "================================================"
echo ""

# Example 2: Dinner for family
echo "Example 2: Family dinner"
curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "prompt": "Healthy dinner for 4 people, vegetarian"
    }
  }' | jq '{status, response: .result.response[:200], execution_time_ms, cost}'

echo ""
echo "================================================"
echo ""

# Example 3: Snack ideas
echo "Example 3: Snack ideas"
curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "prompt": "What are good protein-rich snacks?"
    }
  }' | jq '{status, response: .result.response[:200], execution_time_ms, cost}'

echo ""
echo "================================================"
echo "✅ Tests complete!"
echo "View in UI: http://localhost:3001/invocations"
echo ""
