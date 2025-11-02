#!/bin/bash
# Register Model A Agent with AgentOS

# Set your JWT token
JWT_TOKEN="eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Ijp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA"

RUNTIME_URL="http://localhost:8082"

echo "🚀 Registering Model A Agent: calculator-agent"
echo ""

# Step 1: Register the agent
echo "Step 1: Creating agent..."
RESPONSE=$(curl -s -X POST "$RUNTIME_URL/v1/agents/modelA" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "calculator-agent",
    "description": "A simple calculator agent for basic math operations",
    "runtime": "python3.11",
    "metadata": {
      "version": "1.0.0",
      "author": "AgentOS Team",
      "capabilities": ["addition", "multiplication", "averaging"]
    }
  }')

echo "$RESPONSE" | jq '.'

# Extract agent_id
AGENT_ID=$(echo "$RESPONSE" | jq -r '.agent_id')

if [ "$AGENT_ID" = "null" ] || [ -z "$AGENT_ID" ]; then
  echo "❌ Failed to create agent"
  exit 1
fi

echo ""
echo "✅ Agent created with ID: $AGENT_ID"
echo ""

# Step 2: Package and upload code
echo "Step 2: Packaging agent code..."
cd "$(dirname "$0")"
zip -q agent.zip agent.py requirements.txt

echo "Step 3: Uploading code artifact..."
UPLOAD_RESPONSE=$(curl -s -X PUT "$RUNTIME_URL/v1/agents/$AGENT_ID/artifact" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@agent.zip")

echo "$UPLOAD_RESPONSE" | jq '.'

# Check build status
DEPLOYMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.deployment_id')
BUILD_STATUS=$(echo "$UPLOAD_RESPONSE" | jq -r '.status')

if [ "$BUILD_STATUS" != "SUCCESS" ]; then
  echo "❌ Build failed"
  exit 1
fi

echo ""
echo "✅ Code uploaded and built: $DEPLOYMENT_ID"
echo ""

# Build completed immediately

rm -f agent.zip

echo ""
echo "================================================"
echo "✅ Agent Registration Complete!"
echo "================================================"
echo "Agent ID: $AGENT_ID"
echo "Name: calculator-agent"
echo ""
echo "Test the agent with:"
echo "  ./invoke_agent.sh $AGENT_ID"
echo ""
