#!/bin/bash
# Quick test script for the FastAPI wrapper

set -e

echo "🧪 Testing Meal Planning Agent FastAPI Wrapper"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if wrapper is running
echo "1. Checking if wrapper is running..."
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Wrapper is running"
else
    echo -e "${RED}✗${NC} Wrapper is NOT running"
    echo ""
    echo "Start it with: python model_b_sample.py"
    exit 1
fi

# Health check
echo ""
echo "2. Testing health check..."
HEALTH=$(curl -s http://localhost:9000/health)
echo "$HEALTH" | jq '.'
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "${GREEN}✓${NC} Health check passed"
else
    echo -e "${RED}✗${NC} Health check failed"
    exit 1
fi

# Test invocation
echo ""
echo "3. Testing agent invocation..."
RESPONSE=$(curl -s -X POST http://localhost:9000/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Give me a quick healthy breakfast idea"}')

echo "Response preview:"
echo "$RESPONSE" | jq '{
  output: (.output | .[0:200] + "..."),
  execution_time_ms,
  timestamp,
  telemetry_quality: .telemetry.metadata.telemetry_quality
}'

if echo "$RESPONSE" | jq -e '.output' > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Invocation successful"
else
    echo -e "${RED}✗${NC} Invocation failed"
    echo "Full response:"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

# Check telemetry
echo ""
echo "4. Verifying telemetry..."
TELEMETRY_QUALITY=$(echo "$RESPONSE" | jq -r '.telemetry.metadata.telemetry_quality // "none"')
if [ "$TELEMETRY_QUALITY" = "verified" ]; then
    echo -e "${GREEN}✓${NC} Telemetry quality: verified"
else
    echo -e "${YELLOW}⚠${NC}  Telemetry quality: $TELEMETRY_QUALITY"
fi

echo ""
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Register with AgentOS:"
echo "     curl -X POST http://localhost:8082/v1/agents/modelB \\"
echo "       -H \"Authorization: Bearer test-token\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"name\": \"meal-planner\", \"endpoint_url\": \"http://host.docker.internal:9000/invoke\", \"auth\": {\"type\": \"none\"}, \"rate_limit\": {\"rps\": 5, \"burst\": 10}}'"
echo ""
echo "  2. View in AgentOS UI: http://localhost:3001"
