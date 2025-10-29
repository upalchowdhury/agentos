#!/bin/bash
# Deploy Sentiment Analyzer Agent to AgentOS Runtime

set -e

RUNTIME_URL="${RUNTIME_URL:-http://localhost:8000}"
AGENT_FILE="sentiment_agent_v2.py"

echo "Deploying Sentiment Analyzer Agent to AgentOS Runtime"
echo "Runtime URL: $RUNTIME_URL"
echo ""

# Read agent code
if [ ! -f "$AGENT_FILE" ]; then
    echo "Error: $AGENT_FILE not found"
    exit 1
fi

AGENT_CODE=$(cat "$AGENT_FILE")

# Create deployment payload
cat > /tmp/agent_deploy.json <<EOF
{
  "agent_id": "sentiment-analyzer-001",
  "name": "Sentiment Analyzer",
  "description": "Analyzes text sentiment and logs detailed usage metrics for monitoring",
  "code": $(echo "$AGENT_CODE" | jq -Rs .),
  "requirements": []
}
EOF

echo "Deploying agent..."
RESPONSE=$(curl -s -X POST "$RUNTIME_URL/api/v1/agents/deploy" \
  -H "Content-Type: application/json" \
  -d @/tmp/agent_deploy.json)

echo "Response:"
echo "$RESPONSE" | jq .

# Check if deployment was successful
if echo "$RESPONSE" | jq -e '.deployment_id' > /dev/null 2>&1; then
    DEPLOYMENT_ID=$(echo "$RESPONSE" | jq -r '.deployment_id')
    echo ""
    echo "✅ Agent deployed successfully!"
    echo "Deployment ID: $DEPLOYMENT_ID"
    echo ""
    echo "To invoke the agent, run:"
    echo "  ./invoke_agent.sh"
else
    echo ""
    echo "❌ Deployment failed"
    echo "Check the error message above"
    exit 1
fi

# Cleanup
rm -f /tmp/agent_deploy.json
