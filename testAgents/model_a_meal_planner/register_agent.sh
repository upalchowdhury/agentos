#!/bin/bash
# Register Meal Planner Agent (Model A) with AgentOS

JWT_TOKEN="eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6YWdlbnQ6aXNzdWVyIiwic3ViIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsImlhdCI6MTc2MjAxOTk4MSwiZXhwIjoxNzY5Nzk1OTgxLCJ2YyI6eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiQWdlbnRDcmVkZW50aWFsIl0sImNyZWRlbnRpYWxTdWJqZWN0Injp7ImlkIjoiZGlkOmFnZW50OmJhNDc0NDYwLWYyNGItNDhmMy05MjZjLTZmZDk0OGUyMDFhYyIsInJvbGUiOiJhZG1pbiIsInBlcm1pc3Npb25zIjpbInJlZ2lzdGVyX2FnZW50IiwiaW52b2tlX2FnZW50Il19fX0.EEXnereWElWqMizudHu5VH51ri-CL6bdw8vw4O0PaVrGPfxuN489dWYgGRAiWzrUagGd1SP5R90dVIcwuyIiAA"

RUNTIME_URL="http://localhost:8082"

# Load from .env file if present
if [ -f .env ]; then
  echo "📄 Loading environment from .env file..."
  export $(cat .env | grep -v '^#' | xargs)
fi

# Check for API key
if [ -z "$GOOGLE_API_KEY" ]; then
  echo "⚠️  WARNING: GOOGLE_API_KEY not set"
  echo "The agent will fail without it."
  echo ""
  echo "Set it by creating a .env file:"
  echo "  echo 'GOOGLE_API_KEY=your-key-here' > .env"
  echo ""
  echo "Or export it:"
  echo "  export GOOGLE_API_KEY='your-key-here'"
  echo ""
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

echo "🍽️  Registering Meal Planner Agent (Model A)"
echo ""

# Step 1: Create agent
echo "Step 1: Creating agent..."
RESPONSE=$(curl -s -X POST "$RUNTIME_URL/v1/agents/modelA" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "meal-planner-a",
    "description": "AI meal planning assistant using Gemini 2.0 Flash",
    "runtime": "python3.11",
    "metadata": {
      "version": "1.0.0",
      "model": "gemini-2.0-flash-exp",
      "requires_api_key": true
    },
    "env_vars": {
      "GOOGLE_API_KEY": "'"$GOOGLE_API_KEY"'"
    }
  }')

echo "$RESPONSE" | jq '.'

AGENT_ID=$(echo "$RESPONSE" | jq -r '.agent_id')

if [ "$AGENT_ID" = "null" ] || [ -z "$AGENT_ID" ]; then
  echo "❌ Failed to create agent"
  exit 1
fi

echo ""
echo "✅ Agent created: $AGENT_ID"
echo ""

# Step 2: Package code
echo "Step 2: Packaging code..."
cd "$(dirname "$0")"
zip -q agent.zip agent.py requirements.txt

# Step 3: Upload
echo "Step 3: Uploading artifact..."
UPLOAD_RESPONSE=$(curl -s -X PUT "$RUNTIME_URL/v1/agents/$AGENT_ID/artifact" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@agent.zip")

echo "$UPLOAD_RESPONSE" | jq '.'

DEPLOYMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.deployment_id')
BUILD_STATUS=$(echo "$UPLOAD_RESPONSE" | jq -r '.status')

if [ "$BUILD_STATUS" != "SUCCESS" ]; then
  echo "❌ Build failed"
  exit 1
fi

echo ""
echo "✅ Code uploaded and built: $DEPLOYMENT_ID"
echo ""

# Build completed immediately (no waiting needed)

rm -f agent.zip

echo ""
echo "================================================"
echo "✅ Meal Planner Agent Deployed!"
echo "================================================"
echo "Agent ID: $AGENT_ID"
echo "Name: meal-planner-a"
echo "Model: Gemini 2.0 Flash"
echo ""
echo "Test with:"
echo "  ./invoke_agent.sh $AGENT_ID"
echo ""
