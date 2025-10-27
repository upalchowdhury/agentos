#!/bin/bash

# Quick Test Script for Agent Runtime with Logging
# This script helps you quickly test agent deployment and verify logging

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "AGENT RUNTIME - QUICK TEST"
echo "========================================"
echo ""

# Check if PostgreSQL is running
echo "1. Checking PostgreSQL..."
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        echo "   ✓ PostgreSQL is running"
    else
        echo "   ✗ PostgreSQL is not running on localhost:5432"
        echo ""
        echo "Start PostgreSQL with Docker:"
        echo "   docker run --name agentos-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=agentos -p 5432:5432 -d postgres:16-alpine"
        exit 1
    fi
else
    echo "   ⚠ pg_isready not found, skipping check"
fi

# Check if database schema exists
echo ""
echo "2. Checking database schema..."
if PGPASSWORD=postgres psql -h localhost -U postgres -d agentos -c "SELECT 1 FROM agent_deployments LIMIT 1;" &> /dev/null; then
    echo "   ✓ Database schema exists"
else
    echo "   ✗ Database schema missing"
    echo ""
    echo "Creating schema..."
    PGPASSWORD=postgres psql -h localhost -U postgres -d agentos -f "${SCRIPT_DIR}/../../infra/migrations/004_runtime_schema.sql" 2>&1 | grep -v "already exists" || true
    echo "   ✓ Schema created"
fi

# Create .env if it doesn't exist
echo ""
echo "3. Checking configuration..."
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo "   Creating .env file..."
    cat > "${SCRIPT_DIR}/.env" <<EOF
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DEBUG=true
HOST=0.0.0.0
PORT=8000
EOF
    echo "   ✓ Configuration created"
else
    echo "   ✓ Configuration exists"
fi

# Check Python dependencies
echo ""
echo "4. Checking Python dependencies..."
if python3 -c "import fastapi, uvicorn, asyncpg" &> /dev/null; then
    echo "   ✓ Dependencies installed"
else
    echo "   ✗ Dependencies missing"
    echo ""
    echo "Installing dependencies..."
    pip install -r "${SCRIPT_DIR}/requirements.txt"
    echo "   ✓ Dependencies installed"
fi

echo ""
echo "========================================"
echo "SETUP COMPLETE"
echo "========================================"
echo ""
echo "Now run the test:"
echo ""
echo "Terminal 1 (Server):"
echo "  cd ${SCRIPT_DIR}"
echo "  python -m src.main"
echo ""
echo "Terminal 2 (Test):"
echo "  cd ${SCRIPT_DIR}"
echo "  python test_simple_agent.py"
echo ""
echo "Watch Terminal 1 for log entries like:"
echo "  INFO - Deployed agent simple-calculator with deployment_id <uuid>"
echo "  INFO - Invoked agent simple-calculator, invocation_id <uuid>, status SUCCESS"
echo ""
echo "========================================"
