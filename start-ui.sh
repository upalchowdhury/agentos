#!/bin/bash

echo "=========================================="
echo "Starting Agent Economy OS Web UI"
echo "=========================================="
echo ""

cd services/web-ui

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

echo "Starting development server..."
echo ""
echo "UI will be available at: http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

npm run dev
