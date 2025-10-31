#!/bin/bash
# Quick API endpoint verification script

BASE_URL="${BASE_URL:-http://localhost:8000}"
USER_ID="test-verify-$(date +%s)"

echo "=== Testing AgentOS API Endpoints ==="
echo "Base URL: $BASE_URL"
echo ""

# Test health
echo "1. Health check:"
curl -s "$BASE_URL/health" | jq -c .
echo ""

# List all available endpoints
echo "2. Available endpoints:"
curl -s "$BASE_URL/openapi.json" | jq -r '.paths | keys[]' | sort
echo ""

# Test Model A deploy (if available)
echo "3. Testing Model A deploy:"
DEPLOY_RESP=$(curl -s -X POST "$BASE_URL/v1/agents/modelA" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: $USER_ID" \
  -d '{
    "name": "test-agent",
    "code": "def handle(input_data): return {\"result\": \"test\"}",
    "owner_id": "'"$USER_ID"'"
  }')
echo "$DEPLOY_RESP" | jq -c '{status: (if .agent_id then "success" else "failed" end), agent_id: .agent_id, detail: .detail}'
echo ""

# Check if observability module exists
echo "4. Checking observability implementation:"
if [ -f "services/runtime/src/api/observability.py" ]; then
    echo "✓ observability.py exists ($(wc -l < services/runtime/src/api/observability.py) lines)"
    grep -c "@router.get" services/runtime/src/api/observability.py | xargs echo "  - Number of GET endpoints:"
else
    echo "✗ observability.py not found"
fi
echo ""

# Check if telemetry ingest exists  
echo "5. Checking telemetry ingest implementation:"
if [ -f "services/runtime/src/api/telemetry_ingest.py" ]; then
    echo "✓ telemetry_ingest.py exists ($(wc -l < services/runtime/src/api/telemetry_ingest.py) lines)"
else
    echo "✗ telemetry_ingest.py not found"
fi
echo ""

# Check SDK
echo "6. Checking Python SDK:"
if [ -d "libraries/sdk-python/agentos_sdk" ]; then
    echo "✓ SDK exists"
    ls -1 libraries/sdk-python/agentos_sdk/*.py | xargs -I {} basename {}
else
    echo "✗ SDK not found"
fi
echo ""

# Check example
echo "7. Checking example agent:"
if [ -f "examples/external-agent-with-sdk/main.py" ]; then
    echo "✓ Example exists ($(wc -l < examples/external-agent-with-sdk/main.py) lines)"
else
    echo "✗ Example not found"
fi
echo ""

# Check tests
echo "8. Checking integration tests:"
if [ -f "tests/integration/test_prd_user_stories.py" ]; then
    echo "✓ Tests exist ($(wc -l < tests/integration/test_prd_user_stories.py) lines)"
    grep -c "async def test_us_" tests/integration/test_prd_user_stories.py | xargs echo "  - Number of user story tests:"
else
    echo "✗ Tests not found"
fi
echo ""

# Check OPA client enhancements
echo "9. Checking OPA governance features:"
if grep -q "domain_allowlist" services/runtime/src/opa_client.py 2>/dev/null; then
    echo "✓ Domain allowlist implemented"
else
    echo "✗ Domain allowlist not found"
fi
if grep -q "pii_redaction" services/runtime/src/opa_client.py 2>/dev/null; then
    echo "✓ PII redaction implemented"
else
    echo "✗ PII redaction not found"
fi
echo ""

echo "=== Summary ==="
echo "Files created in this session:"
echo "  - libraries/sdk-python/ (SDK)"
echo "  - services/runtime/src/api/telemetry_ingest.py (NEW)"
echo "  - examples/external-agent-with-sdk/ (NEW)"
echo "  - tests/integration/test_prd_user_stories.py (NEW)"
echo "  - scripts/verify_prd_implementation.sh (NEW)"
echo "  - Enhanced: services/runtime/src/opa_client.py (domain allowlist)"
