.PHONY: help dev test migrate seed clean
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
KUBECTL := kubectl
PSQL := docker exec -i agentos-postgres psql -U postgres -d agentos

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

##@ General

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

dev: ## Run all services locally with hot reload
	@echo "$(GREEN)Starting development environment...$(NC)"
	cd ../services/runtime && $(PYTHON) -m src.main &
	@echo "$(GREEN)Runtime service started on http://localhost:8000$(NC)"

runtime/dev: ## Run runtime service locally
	@echo "$(GREEN)Starting runtime service...$(NC)"
	cd ../services/runtime && $(PYTHON) -m src.main

runtime/install: ## Install runtime service dependencies
	@echo "$(GREEN)Installing runtime service dependencies...$(NC)"
	cd ../services/runtime && $(PIP) install -r requirements.txt

registry/dev: ## Run registry service locally (stub)
	@echo "$(YELLOW)Registry service not yet implemented$(NC)"

observability/dev: ## Run observability service locally (stub)
	@echo "$(YELLOW)Observability service not yet implemented$(NC)"

##@ Database

migrate: ## Run all database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(PSQL) < ../infra/migrations/001_initial_schema.sql
	$(PSQL) < ../infra/migrations/003_rbac_schema.sql
	$(PSQL) < ../infra/migrations/004_runtime_schema.sql
	$(PSQL) < ../infra/migrations/005_enhanced_runtime_schema.sql
	@echo "$(GREEN)✓ Migrations complete$(NC)"

migrate/status: ## Check migration status
	@echo "$(GREEN)Checking database schema...$(NC)"
	$(PSQL) -c "\dt"

migrate/rollback: ## Rollback last migration (manual)
	@echo "$(RED)Manual rollback required - check migration files$(NC)"

db/reset: ## Reset database (DESTRUCTIVE)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	docker exec agentos-postgres psql -U postgres -c "DROP DATABASE IF EXISTS agentos;"
	docker exec agentos-postgres psql -U postgres -c "CREATE DATABASE agentos;"
	@$(MAKE) migrate
	@echo "$(GREEN)✓ Database reset complete$(NC)"

##@ Seeding

seed: seed/agents seed/users ## Seed all demo data

seed/agents: ## Create demo agents
	@echo "$(GREEN)Creating demo agents...$(NC)"
	cd ../services/runtime && $(PYTHON) deploy_monitored_agent.py
	@echo "$(GREEN)✓ Demo agents created$(NC)"

seed/users: ## Create demo users (stub)
	@echo "$(YELLOW)User seeding not yet implemented$(NC)"

##@ Testing

test: test/unit test/integration ## Run all tests

test/unit: ## Run unit tests
	@echo "$(GREEN)Running unit tests...$(NC)"
	cd ../services/runtime && $(PYTHON) -m pytest tests/unit -v

test/integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	cd ../services/runtime && $(PYTHON) -m pytest tests/integration -v

test/e2e: ## Run end-to-end tests
	@echo "$(GREEN)Running e2e tests...$(NC)"
	cd ../services/runtime && $(PYTHON) -m pytest tests/e2e -v

test/coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	cd ../services/runtime && $(PYTHON) -m pytest --cov=src --cov-report=html --cov-report=term

##@ Kubernetes

kind-up: ## Start local kind cluster
	@echo "$(GREEN)Starting kind cluster...$(NC)"
	kind create cluster --name agentos --config kind/cluster-config.yaml
	@$(MAKE) kind-setup
	@echo "$(GREEN)✓ Kind cluster ready$(NC)"

kind-down: ## Stop local kind cluster
	@echo "$(RED)Stopping kind cluster...$(NC)"
	kind delete cluster --name agentos

kind-setup: ## Setup kind cluster (ingress, etc)
	@echo "$(GREEN)Setting up kind cluster...$(NC)"
	$(KUBECTL) apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	$(KUBECTL) wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=90s
	@echo "$(GREEN)✓ Ingress controller ready$(NC)"

runtime/deploy: ## Deploy runtime service to k8s
	@echo "$(GREEN)Deploying runtime service...$(NC)"
	$(KUBECTL) apply -f ../k8s/runtime/

registry/deploy: ## Deploy registry service to k8s
	@echo "$(YELLOW)Registry service not yet implemented$(NC)"

observability/deploy: ## Deploy observability service to k8s
	@echo "$(YELLOW)Observability service not yet implemented$(NC)"

k8s/status: ## Show k8s resources
	@echo "$(GREEN)AgentOS Resources:$(NC)"
	$(KUBECTL) get all -n agentos

##@ Monitoring

monitor: ## Run monitoring dashboard
	@echo "$(GREEN)Starting monitoring dashboard...$(NC)"
	cd ../services/runtime && $(PYTHON) monitor_agent.py

security: ## Run security audit
	@echo "$(GREEN)Running security audit...$(NC)"
	cd ../services/runtime && ./check_security.sh

logs: ## Tail runtime service logs
	@echo "$(GREEN)Tailing runtime service logs...$(NC)"
	$(KUBECTL) logs -f -l app=runtime-service -n agentos

##@ OPA

opa/run: ## Run OPA server locally
	@echo "$(GREEN)Starting OPA server...$(NC)"
	docker run -d --name opa \
		-p 8181:8181 \
		-v $(PWD)/../infra/opa:/policies \
		openpolicyagent/opa:latest \
		run --server --addr :8181 /policies

opa/stop: ## Stop OPA server
	@echo "$(RED)Stopping OPA server...$(NC)"
	docker stop opa && docker rm opa

opa/test: ## Test OPA policies
	@echo "$(GREEN)Testing OPA policies...$(NC)"
	docker run --rm \
		-v $(PWD)/../infra/opa:/policies \
		openpolicyagent/opa:latest \
		test /policies -v

opa/query: ## Query OPA for test decision
	@echo "$(GREEN)Querying OPA...$(NC)"
	curl -X POST http://localhost:8181/v1/data/agentos/authz \
		-H "Content-Type: application/json" \
		-d '{"input": {"subject_type": "user", "subject": {"id": "user_123", "roles": ["agent:executor"]}, "agent_id": "agent_456", "agent": {"owner_id": "user_123"}}}'

##@ CI/CD

lint: ## Run linters
	@echo "$(GREEN)Running linters...$(NC)"
	cd ../services/runtime && $(PYTHON) -m pylint src/
	cd ../services/runtime && $(PYTHON) -m black --check src/
	cd ../services/runtime && $(PYTHON) -m mypy src/

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	cd ../services/runtime && $(PYTHON) -m black src/
	cd ../services/runtime && $(PYTHON) -m isort src/

openapi/validate: ## Validate OpenAPI spec
	@echo "$(GREEN)Validating OpenAPI spec...$(NC)"
	docker run --rm -v $(PWD)/../openapi:/spec \
		openapitools/openapi-generator-cli validate -i /spec/api.yaml

openapi/generate: ## Generate client SDKs from OpenAPI spec
	@echo "$(GREEN)Generating client SDKs...$(NC)"
	docker run --rm -v $(PWD)/../openapi:/spec -v $(PWD)/../clients:/out \
		openapitools/openapi-generator-cli generate \
		-i /spec/api.yaml \
		-g python \
		-o /out/python

##@ Utilities

clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find .. -type d -name __pycache__ -exec rm -rf {} +
	find .. -type f -name "*.pyc" -delete
	find .. -type d -name ".pytest_cache" -exec rm -rf {} +
	find .. -type d -name "htmlcov" -exec rm -rf {} +
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

ps: ## Show running services
	@echo "$(GREEN)Running services:$(NC)"
	@docker ps --filter "name=agentos" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@ps aux | grep -E "(python.*src.main|streamlit)" | grep -v grep || echo "No local services running"

install: runtime/install ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install -r ../services/runtime/requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

##@ Quick Start

quick-start: migrate seed runtime/dev ## Quick start: migrate + seed + run
	@echo "$(GREEN)╔════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║  AgentOS Runtime Ready!                            ║$(NC)"
	@echo "$(GREEN)║  API: http://localhost:8000                        ║$(NC)"
	@echo "$(GREEN)║  Docs: http://localhost:8000/docs                  ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════╝$(NC)"

demo: ## Run complete demo flow
	@echo "$(GREEN)Running demo flow...$(NC)"
	@$(MAKE) seed/agents
	@sleep 2
	@$(MAKE) monitor
