#!/bin/bash
# Invoke Sentiment Analyzer Agent

set -e

RUNTIME_URL="${RUNTIME_URL:-http://localhost:8000}"
AGENT_ID="sentiment-analyzer-001"

echo "Invoking Sentiment Analyzer Agent"
echo "Agent ID: $AGENT_ID"
echo ""

# Test cases
declare -a TEST_CASES=(
    '{"text": "This product is absolutely amazing! I love how well it works. Best purchase ever!"}'
    '{"text": "Terrible experience. Very disappointed and frustrated with the poor quality."}'
    '{"text": "The item arrived on time. It works as described. Nothing remarkable."}'
    '{"text": "I am so happy with this service! Excellent customer support and fast delivery!"}'
)

for i in "${!TEST_CASES[@]}"; do
    TEST_NUM=$((i + 1))
    INPUT="${TEST_CASES[$i]}"
    
    echo "Test $TEST_NUM:"
    echo "Input: $INPUT"
    echo ""
    
    # Create invocation payload
    cat > /tmp/invoke.json <<EOF
{
  "agent_id": "$AGENT_ID",
  "input_data": $INPUT
}
EOF
    
    echo "Invoking agent..."
    RESPONSE=$(curl -s -X POST "$RUNTIME_URL/api/v1/agents/invoke" \
      -H "Content-Type: application/json" \
      -d @/tmp/invoke.json)
    
    echo "Response:"
    echo "$RESPONSE" | jq .
    echo ""
    echo "=" * 60
    echo ""
    
    # Small delay between requests
    sleep 1
done

# Check agent status
echo "Checking agent status..."
STATUS=$(curl -s "$RUNTIME_URL/api/v1/agents/$AGENT_ID/status")
echo "Agent Status:"
echo "$STATUS" | jq .

# Cleanup
rm -f /tmp/invoke.json

echo ""
echo "✅ Agent invocation tests completed!"
echo ""
echo "Check the runtime logs to see detailed metrics:"
echo "  kubectl logs -n agentos deployment/runtime --tail=100"
