#!/bin/bash
set -e

echo "🚀 Setting up Agent Economy OS development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose required"; exit 1; }

echo "✅ Prerequisites check passed"

# Start infrastructure
echo "📦 Starting infrastructure services..."
docker-compose -f docker-compose.dev.yaml up -d postgres redis qdrant clickhouse

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.dev.yaml exec -T postgres psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/001_initial_schema.sql || true
docker-compose -f docker-compose.dev.yaml exec -T postgres psql -U postgres -d agentos -f /docker-entrypoint-initdb.d/002_add_indexes.sql || true

# Start application services
echo "🎯 Starting application services..."
docker-compose -f docker-compose.dev.yaml up -d

echo "✨ Development environment ready!"
echo ""
echo "Services available at:"
echo "  - Gateway:       http://localhost:8080"
echo "  - Identity:      http://localhost:3000"
echo "  - Memory:        http://localhost:8000"
echo "  - Policy Engine: http://localhost:8081"
echo "  - PostgreSQL:    localhost:5432"
echo "  - Redis:         localhost:6379"
echo "  - Qdrant:        http://localhost:6333"
echo ""
echo "View logs: docker-compose -f docker-compose.dev.yaml logs -f"
echo "Stop services: docker-compose -f docker-compose.dev.yaml down"
