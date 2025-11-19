#!/bin/bash

echo "=========================================="
echo "Starting AgentOS Web UI (Updated)"
echo "=========================================="
echo ""

cd web-ui

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

echo "Starting development server..."
echo "UI will be available at: http://localhost:5173"
echo ""

npm run dev
