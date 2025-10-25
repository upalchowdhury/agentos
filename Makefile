.PHONY: help build test deploy clean dev-up dev-down

help:
	@echo "Agent Economy OS - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up       - Start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Build:"
	@echo "  make build        - Build all services"
	@echo "  make build-gateway    - Build gateway service"
	@echo "  make build-identity   - Build identity service"
	@echo "  make build-memory     - Build memory service"
	@echo "  make build-policy     - Build policy engine"
	@echo ""
	@echo "Deploy:"
	@echo "  make deploy       - Deploy to Kubernetes"
	@echo "  make clean        - Clean build artifacts"

dev-up:
	@./scripts/dev-setup.sh

dev-down:
	@docker-compose -f docker-compose.dev.yaml down

test:
	@./scripts/test-all.sh

build: build-gateway build-identity build-memory build-policy

build-gateway:
	@echo "Building Gateway service..."
	@cd services/gateway && docker build -t agentos/gateway:latest .

build-identity:
	@echo "Building Identity service..."
	@cd services/identity && docker build -t agentos/identity:latest .

build-memory:
	@echo "Building Memory service..."
	@cd services/memory && docker build -t agentos/memory:latest .

build-policy:
	@echo "Building Policy Engine..."
	@cd services/policy-engine && docker build -t agentos/policy-engine:latest .

deploy:
	@echo "Deploying to Kubernetes..."
	@helm upgrade --install gateway ./infra/helm/gateway --namespace agentos --create-namespace

clean:
	@echo "Cleaning build artifacts..."
	@cd services/gateway && go clean
	@cd services/identity && rm -rf dist node_modules
	@cd services/memory && rm -rf dist __pycache__ .pytest_cache
	@cd services/policy-engine && cargo clean
