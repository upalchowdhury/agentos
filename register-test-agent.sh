#!/bin/bash
# Register the test agent with runtime

set -e

echo "🔧 Registering Model B Test Agent..."

# Register agent
curl -X POST 'http://localhost:30000/v1/catalog/agents?agent_id=550e8400-e29b-41d4-a716-446655440000&name=model-b-test-agent&endpoint=http://test-agent:9000&version=1.0.0'

echo ""
echo ""
echo "✅ Agent registered!"
echo ""
echo "📋 Verify registration:"
curl -s http://localhost:30000/v1/catalog/agents | jq

echo ""
echo ""
echo "🚀 Test invocation:"
curl -X POST http://localhost:30000/v1/agents/550e8400-e29b-41d4-a716-446655440000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "registration_check"}}' | jq

echo ""
echo "✨ All set! Visit http://localhost:30080 and click 'Invoke Test Agent'"
