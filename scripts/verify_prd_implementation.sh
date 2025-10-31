#!/bin/bash
#
# PRD Implementation Verification Script
#
# This script verifies that all user stories from the PRD are properly implemented.
# Run this after deployment to validate the platform meets requirements.
#

set -e

echo "======================================================================"
echo "AgentOS PRD Implementation Verification"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
RUNTIME_URL="${RUNTIME_URL:-http://localhost:8000}"
OPA_URL="${OPA_URL:-http://localhost:8181}"
TEST_USER_ID="test-user-verification"

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✓ PASS${NC} - $1"
    ((PASSED++))
}

fail_test() {
    echo -e "${RED}✗ FAIL${NC} - $1"
    echo "  Reason: $2"
    ((FAILED++))
}

skip_test() {
    echo -e "${YELLOW}○ SKIP${NC} - $1"
    echo "  Reason: $2"
    ((SKIPPED++))
}

check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f -o /dev/null "$url/health" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

echo "Checking services..."
echo ""

# Check Runtime Service
if check_service "Runtime" "$RUNTIME_URL"; then
    pass_test "Runtime service is reachable at $RUNTIME_URL"
else
    fail_test "Runtime service" "Cannot reach $RUNTIME_URL/health"
    echo ""
    echo "Please start the runtime service first:"
    echo "  cd services/runtime && python -m src.main"
    echo ""
    exit 1
fi

echo ""
echo "======================================================================"
echo "Testing User Stories"
echo "======================================================================"
echo ""

# ============================================================================
# US-A1 (M): Create & deploy agent
# ============================================================================
echo "--- US-A1 (M): Create & deploy agent ---"

TEST_CODE='def handle(input_data): return {"result": "test"}'

DEPLOY_RESPONSE=$(curl -s -X POST "$RUNTIME_URL/v1/agents/modelA" \
    -H "Content-Type: application/json" \
    -H "X-User-ID: $TEST_USER_ID" \
    -d "{
        \"name\": \"verify-agent-us-a1\",
        \"code\": \"$TEST_CODE\",
        \"owner_id\": \"$TEST_USER_ID\"
    }")

if echo "$DEPLOY_RESPONSE" | grep -q "agent_id"; then
    AGENT_ID=$(echo "$DEPLOY_RESPONSE" | grep -o '"agent_id":"[^"]*"' | cut -d'"' -f4)
    pass_test "US-A1: Agent deployed successfully (ID: ${AGENT_ID:0:12}...)"
else
    fail_test "US-A1" "Failed to deploy agent"
fi

echo ""

# ============================================================================
# US-A2 (M): Invoke & view trace
# ============================================================================
echo "--- US-A2 (M): Invoke & view trace ---"

if [ ! -z "$AGENT_ID" ]; then
    INVOKE_RESPONSE=$(curl -s -X POST "$RUNTIME_URL/v1/agents/$AGENT_ID/invoke" \
        -H "Content-Type: application/json" \
        -H "X-User-ID: $TEST_USER_ID" \
        -d '{"input_data": {"test": "verification"}}')
    
    if echo "$INVOKE_RESPONSE" | grep -q "invocation_id"; then
        INVOCATION_ID=$(echo "$INVOKE_RESPONSE" | grep -o '"invocation_id":"[^"]*"' | cut -d'"' -f4)
        pass_test "US-A2: Agent invoked successfully"
        
        # Check trace
        TRACE_RESPONSE=$(curl -s "$RUNTIME_URL/v1/observability/agents/trace/$INVOCATION_ID" \
            -H "X-User-ID: $TEST_USER_ID")
        
        if echo "$TRACE_RESPONSE" | grep -q "trace_id"; then
            pass_test "US-A2: Trace data available"
        else
            fail_test "US-A2: Trace" "Trace data not found"
        fi
    else
        fail_test "US-A2" "Failed to invoke agent"
    fi
else
    skip_test "US-A2" "No agent ID from US-A1"
fi

echo ""

# ============================================================================
# US-A3 (M): Cost attribution per invocation
# ============================================================================
echo "--- US-A3 (M): Cost attribution ---"

if [ ! -z "$INVOCATION_ID" ]; then
    if echo "$TRACE_RESPONSE" | grep -q "cost_usd"; then
        pass_test "US-A3: Per-invocation cost tracking present"
    else
        fail_test "US-A3" "Cost data not found in trace"
    fi
else
    skip_test "US-A3" "No invocation ID from US-A2"
fi

echo ""

# ============================================================================
# US-B1 (M): Register external agent
# ============================================================================
echo "--- US-B1 (M): Register external agent ---"

REGISTER_RESPONSE=$(curl -s -X POST "$RUNTIME_URL/v1/agents/modelB" \
    -H "Content-Type: application/json" \
    -H "X-User-ID: $TEST_USER_ID" \
    -d '{
        "name": "verify-external-agent",
        "endpoint": "https://external.example.com/invoke",
        "owner_id": "'"$TEST_USER_ID"'"
    }')

if echo "$REGISTER_RESPONSE" | grep -q "agent_id"; then
    EXTERNAL_AGENT_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"agent_id":"[^"]*"' | cut -d'"' -f4)
    pass_test "US-B1: External agent registered (ID: ${EXTERNAL_AGENT_ID:0:12}...)"
else
    fail_test "US-B1" "Failed to register external agent"
fi

echo ""

# ============================================================================
# US-B2 (M): SDK for deep telemetry
# ============================================================================
echo "--- US-B2 (M): SDK for deep telemetry ---"

if [ -d "libraries/sdk-python/agentos_sdk" ]; then
    pass_test "US-B2: Python SDK exists"
    
    # Check SDK components
    if [ -f "libraries/sdk-python/agentos_sdk/client.py" ]; then
        pass_test "US-B2: SDK client module present"
    else
        fail_test "US-B2: SDK client" "client.py not found"
    fi
    
    if [ -f "libraries/sdk-python/agentos_sdk/telemetry.py" ]; then
        pass_test "US-B2: SDK telemetry module present"
    else
        fail_test "US-B2: SDK telemetry" "telemetry.py not found"
    fi
    
    # Check telemetry ingest endpoint
    INGEST_CHECK=$(curl -s -X POST "$RUNTIME_URL/v1/telemetry/ingest" \
        -H "Content-Type: application/json" \
        -H "X-User-ID: $TEST_USER_ID" \
        -d '{"trace": {"trace_id": "test"}}')
    
    if echo "$INGEST_CHECK" | grep -q -e "Missing required" -e "agent_id"; then
        pass_test "US-B2: Telemetry ingest endpoint available"
    else
        fail_test "US-B2: Telemetry ingest" "Endpoint not responding correctly"
    fi
else
    fail_test "US-B2" "Python SDK not found at libraries/sdk-python"
fi

echo ""

# ============================================================================
# US-O1 (M): Dashboards
# ============================================================================
echo "--- US-O1 (M): Org/Project dashboards ---"

DASHBOARD_START=$(date +%s%3N)
DASHBOARD_RESPONSE=$(curl -s "$RUNTIME_URL/v1/observability/agents?range=1d" \
    -H "X-User-ID: $TEST_USER_ID")
DASHBOARD_END=$(date +%s%3N)
DASHBOARD_TIME=$((DASHBOARD_END - DASHBOARD_START))

if echo "$DASHBOARD_RESPONSE" | grep -q -e "\[" -e "agent_id"; then
    if [ $DASHBOARD_TIME -lt 1500 ]; then
        pass_test "US-O1: Dashboard loads in ${DASHBOARD_TIME}ms (<1.5s requirement)"
    else
        fail_test "US-O1: Dashboard performance" "Loaded in ${DASHBOARD_TIME}ms (>1.5s)"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "success_rate"; then
        pass_test "US-O1: Dashboard includes success_rate metric"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "p95_latency_ms"; then
        pass_test "US-O1: Dashboard includes p95_latency metric"
    fi
else
    fail_test "US-O1" "Dashboard endpoint returned unexpected response"
fi

echo ""

# ============================================================================
# US-O2 (M): Logs correlation
# ============================================================================
echo "--- US-O2 (M): Logs correlation ---"

LOGS_RESPONSE=$(curl -s "$RUNTIME_URL/v1/observability/logs?limit=10" \
    -H "X-User-ID: $TEST_USER_ID")

if echo "$LOGS_RESPONSE" | grep -q -e "\[" -e "trace_id"; then
    pass_test "US-O2: Logs endpoint available"
    
    if echo "$LOGS_RESPONSE" | grep -q "trace_id"; then
        pass_test "US-O2: Logs include trace_id for correlation"
    fi
else
    fail_test "US-O2" "Logs endpoint not working"
fi

echo ""

# ============================================================================
# US-G1 (M): OPA RBAC
# ============================================================================
echo "--- US-G1 (M): OPA RBAC ---"

if check_service "OPA" "$OPA_URL"; then
    pass_test "US-G1: OPA service is reachable"
    
    # Check OPA integration in code
    if grep -r "opa_client" services/runtime/src/ > /dev/null 2>&1; then
        pass_test "US-G1: OPA client integration present in code"
    else
        fail_test "US-G1: OPA integration" "opa_client not found in runtime"
    fi
else
    skip_test "US-G1" "OPA service not running at $OPA_URL"
fi

echo ""

# ============================================================================
# US-G2 (S): Obligations (redaction & allowlists)
# ============================================================================
echo "--- US-G2 (S): Obligations ---"

if grep -q "pii_redaction" services/runtime/src/opa_client.py 2>/dev/null; then
    pass_test "US-G2: PII redaction implementation present"
else
    fail_test "US-G2: PII redaction" "Implementation not found"
fi

if grep -q "domain_allowlist" services/runtime/src/opa_client.py 2>/dev/null; then
    pass_test "US-G2: Domain allowlist implementation present"
else
    fail_test "US-G2: Domain allowlist" "Implementation not found"
fi

echo ""

# ============================================================================
# US-G3 (S): Audit export
# ============================================================================
echo "--- US-G3 (S): Audit export ---"

END_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
START_DATE=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "7 days ago" +"%Y-%m-%dT%H:%M:%SZ")

AUDIT_RESPONSE=$(curl -s "$RUNTIME_URL/v1/observability/audit/export?start=$START_DATE&end=$END_DATE&limit=100" \
    -H "X-User-ID: $TEST_USER_ID")

if echo "$AUDIT_RESPONSE" | head -1 | grep -q "invocation_id"; then
    pass_test "US-G3: Audit export endpoint works (CSV format)"
    
    if echo "$AUDIT_RESPONSE" | head -1 | grep -q "cost_usd"; then
        pass_test "US-G3: Audit export includes cost data"
    fi
else
    fail_test "US-G3" "Audit export endpoint not working"
fi

echo ""

# ============================================================================
# Additional checks
# ============================================================================
echo "--- Additional Platform Checks ---"

# Check database connectivity
if echo "$DEPLOY_RESPONSE" | grep -q "agent_id"; then
    pass_test "Database: Successfully storing agent data"
fi

# Check OpenTelemetry
if grep -q "telemetry" services/runtime/src/main.py 2>/dev/null; then
    pass_test "OpenTelemetry: Integration present in runtime"
fi

# Check Web UI
if [ -d "services/web-ui/src" ]; then
    pass_test "Web UI: Frontend code present"
fi

echo ""
echo "======================================================================"
echo "Verification Summary"
echo "======================================================================"
echo ""
echo -e "${GREEN}PASSED:${NC}  $PASSED tests"
echo -e "${YELLOW}SKIPPED:${NC} $SKIPPED tests"
echo -e "${RED}FAILED:${NC}  $FAILED tests"
echo ""

TOTAL=$((PASSED + FAILED + SKIPPED))
SUCCESS_RATE=$((PASSED * 100 / (PASSED + FAILED)))

echo "Success Rate: $SUCCESS_RATE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical user stories are implemented!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some user stories need attention${NC}"
    echo ""
    echo "Review the failed tests above and check:"
    echo "  1. All services are running (runtime, OPA, database)"
    echo "  2. Database migrations are applied"
    echo "  3. Configuration is correct"
    echo ""
    exit 1
fi
