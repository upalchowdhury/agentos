#!/bin/bash
set -e

echo "🔨 Building Docker images..."

# Configuration
REGISTRY=${REGISTRY:-agentos}
VERSION=${VERSION:-0.1.0}

# Build Gateway
echo "Building Gateway service..."
cd services/gateway
docker build -t $REGISTRY/gateway:$VERSION -t $REGISTRY/gateway:latest .
cd ../..

# Build Identity
echo "Building Identity service..."
cd services/identity
docker build -t $REGISTRY/identity:$VERSION -t $REGISTRY/identity:latest .
cd ../..

# Build Memory
echo "Building Memory service..."
cd services/memory
docker build -t $REGISTRY/memory:$VERSION -t $REGISTRY/memory:latest .
cd ../..

# Build Policy Engine
echo "Building Policy Engine..."
cd services/policy-engine
docker build -t $REGISTRY/policy-engine:$VERSION -t $REGISTRY/policy-engine:latest .
cd ../..

echo "✅ All images built successfully!"
echo ""
echo "Images:"
echo "  $REGISTRY/gateway:$VERSION"
echo "  $REGISTRY/identity:$VERSION"
echo "  $REGISTRY/memory:$VERSION"
echo "  $REGISTRY/policy-engine:$VERSION"
echo ""
echo "To push to a registry:"
echo "  export REGISTRY=your-registry.io/agentos"
echo "  docker push $REGISTRY/gateway:$VERSION"
echo "  docker push $REGISTRY/identity:$VERSION"
echo "  docker push $REGISTRY/memory:$VERSION"
echo "  docker push $REGISTRY/policy-engine:$VERSION"
