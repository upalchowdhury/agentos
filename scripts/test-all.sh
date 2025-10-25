#!/bin/bash
set -e

echo "🧪 Running all tests..."

# Gateway tests
echo "📦 Testing Gateway service (Go)..."
cd services/gateway && go test -v ./... && cd ../..

# Identity tests  
echo "🆔 Testing Identity service (TypeScript)..."
cd services/identity && npm test && cd ../..

# Memory tests
echo "🧠 Testing Memory service (Python)..."
cd services/memory && pytest && cd ../..

# Policy engine tests
echo "🛡️  Testing Policy Engine (Rust)..."
cd services/policy-engine && cargo test && cd ../..

echo "✅ All tests passed!"
