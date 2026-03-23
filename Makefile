.PHONY: help install dev-install setup-dev up down restart logs health clean clean-image clean-images test test-all lint format type-check pre-commit migrate seed

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color
COMPOSE := docker-compose --env-file .env -f infrastructure/docker-compose.yml
COMPOSE_TEST := $(COMPOSE) --profile test

help: ## Show this help message
	@echo "$(BLUE)Food Delivery - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

## Installation & Setup

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --frozen

dev-install: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	uv sync --frozen --all-extras --all-packages
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)Development environment ready!$(NC)"

setup-dev: ## Bootstrap dev machine (env, deps, dirs)
	@bash scripts/setup-dev.sh

## Docker & Services

up: ## Start all services (docker-compose up -d)
	@echo "$(BLUE)Starting all services...$(NC)"
	$(COMPOSE) up -d
	@echo "$(GREEN)All services started!$(NC)"
	@$(MAKE) health

down: ## Stop all services (docker-compose down)
	@echo "$(YELLOW)Stopping all services...$(NC)"
	$(COMPOSE) down

restart: ## Restart all services
	@$(MAKE) down
	@$(MAKE) up

logs: ## Show logs from all services (use SERVICE=name for specific service)
	@echo "$(BLUE)Showing logs...$(NC)"
ifdef SERVICE
	$(COMPOSE) logs -f $(SERVICE)
else
	$(COMPOSE) logs -f
endif

health: ## Check health of all services
	@echo "$(BLUE)Checking services health...$(NC)"
	@bash scripts/check-health.sh

clean: ## Remove all containers, volumes, and build artifacts
	@echo "$(RED)Cleaning up...$(NC)"
	$(COMPOSE) down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-image: clean-images ## Alias for clean-images

clean-images: ## Remove all containers, volumes, images, and build artifacts
	@echo "$(RED)Cleaning up (including images)...$(NC)"
	$(COMPOSE) down -v --rmi local
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

## Testing & Quality

wait-http: ## Wait for HTTP endpoint (use URL=http://...)
ifndef URL
	@echo "$(RED)Error: Please specify URL (e.g. URL=http://localhost:8001/health)$(NC)"
	@exit 1
endif
	@for i in $$(seq 1 90); do \
		if curl -fsS "$(URL)" >/dev/null 2>&1; then \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "$(RED)Timeout waiting for $(URL)$(NC)"; \
	exit 1

test: ## Run all tests
	@echo "$(BLUE)Running tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if find tests -type f -name "test_*.py" 2>/dev/null | grep -q .; then \
			/opt/venv/bin/pytest; \
		else \
			echo "No root tests found in ./tests; skipping."; \
		fi'

test-all: ## Run repo tests and all service tests
	@echo "$(BLUE)Running all tests in Docker...$(NC)"
	@$(COMPOSE) up -d postgres redis user-service
	@$(MAKE) wait-http URL=http://localhost:8001/health
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if find tests -type f -name "test_*.py" 2>/dev/null | grep -q .; then \
			echo "Running tests..."; \
			/opt/venv/bin/pytest; \
		else \
			echo "No root tests found in ./tests; skipping."; \
		fi; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				echo "Running tests in $$svc..."; \
				(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml); \
			fi; \
		done'

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm test-runner bash -lc 'set -e; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				echo "Running unit tests in $$svc..."; \
				(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml -m unit); \
			fi; \
		done'

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm test-runner bash -lc 'set -e; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				echo "Running integration tests in $$svc..."; \
				(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml -m integration); \
			fi; \
		done'

test-e2e: ## Run end-to-end tests only
	@echo "$(BLUE)Running E2E tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm test-runner bash -lc 'set -e; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				echo "Running E2E tests in $$svc..."; \
				(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml -m e2e); \
			fi; \
		done'

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm test-runner bash -lc 'set -e; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				echo "Running coverage in $$svc..."; \
				(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml); \
			fi; \
		done'

test-service: ## Run tests for a specific service (SERVICE=name)
	@echo "$(BLUE)Running service tests in Docker...$(NC)"
ifdef SERVICE
	@case "$(SERVICE)" in \
		api-gateway) \
			$(COMPOSE) up -d postgres redis user-service; \
			$(MAKE) wait-http URL=http://localhost:8001/health; \
			;; \
		user-service|restaurant-service|order-service) \
			$(COMPOSE) up -d postgres redis; \
			;; \
		*) \
			echo "$(RED)Error: Unknown service '$(SERVICE)'$(NC)"; \
			exit 1; \
			;; \
	esac
	$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; cd services/$(SERVICE) && /opt/venv/bin/pytest -c pyproject.toml'
else
	@echo "$(RED)Error: Please specify SERVICE=name (e.g. SERVICE=user-service)$(NC)"
endif

test-user: ## Run tests for user service
	@$(MAKE) test-service SERVICE=user-service

test-gateway: ## Run tests for API Gateway
	@$(MAKE) test-service SERVICE=api-gateway

test-restaurant: ## Run tests for restaurant service
	@$(MAKE) test-service SERVICE=restaurant-service

test-order: ## Run tests for order service
	@$(MAKE) test-service SERVICE=order-service

lint: ## Run ruff linter
	@echo "$(BLUE)Running linter...$(NC)"
	ruff check .

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format .
	ruff check --fix .
	@echo "$(GREEN)Code formatted!$(NC)"

type-check: ## Run mypy type checker
	@echo "$(BLUE)Running type checker...$(NC)"
	MYPYPATH=shared/src:services/api-gateway mypy services/api-gateway/src
	MYPYPATH=shared/src:services/user-service mypy services/user-service/src
	MYPYPATH=shared/src:services/restaurant-service mypy services/restaurant-service/src
	MYPYPATH=shared/src:services/order-service mypy services/order-service/src
	MYPYPATH=shared/src mypy shared/src

pre-commit: ## Run all pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

## Database

migrate: ## Run database migrations for all services
	@echo "$(BLUE)Running migrations...$(NC)"
	@bash scripts/run-migrations.sh

seed: ## Load seed data into databases
	@echo "$(BLUE)Loading seed data...$(NC)"
	@bash scripts/seed-data.sh

## Development

dev-user: ## Run User Service locally
	@echo "$(BLUE)Starting User Service...$(NC)"
	cd services/user-service && uvicorn src.main:app --reload --port 8001

dev-gateway: ## Run API Gateway locally
	@echo "$(BLUE)Starting API Gateway...$(NC)"
	cd services/api-gateway && uvicorn src.main:app --reload --port 8000

dev-restaurant: ## Run Restaurant Service locally
	@echo "$(BLUE)Starting Restaurant Service...$(NC)"
	cd services/restaurant-service && uvicorn src.main:app --reload --port 8002

dev-order: ## Run Order Service locally
	@echo "$(BLUE)Starting Order Service...$(NC)"
	cd services/order-service && uvicorn src.main:app --reload --port 8003

## Kafka

kafka-topics: ## Create Kafka topics
	@echo "$(BLUE)Creating Kafka topics...$(NC)"
	@bash infrastructure/kafka/create-topics.sh

kafka-console: ## Open Kafka console consumer (specify TOPIC=topic-name)
ifdef TOPIC
	docker exec -it food-delivery-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic $(TOPIC) --from-beginning
else
	@echo "$(RED)Error: Please specify TOPIC=topic-name$(NC)"
endif

## Utilities

shell-postgres: ## Open PostgreSQL shell
	docker exec -it food-delivery-postgres psql -U postgres

shell-redis: ## Open Redis CLI
	docker exec -it food-delivery-redis redis-cli

shell-kafka: ## Open Kafka container shell
	docker exec -it food-delivery-kafka /bin/bash

openapi: ## Generate OpenAPI specs for all services
	@echo "$(BLUE)Generating OpenAPI specifications...$(NC)"
	@bash scripts/generate-openapi.sh

## Monitoring

stats: ## Show container stats
	docker stats

ps: ## Show running containers
	$(COMPOSE) ps
