.PHONY: help install dev-install setup-dev docker-ready up down restart logs health clean clean-image clean-images test test-all test-all-full test-unit test-integration test-e2e test-cov test-deps-up test-e2e-deps-up test-service-prepare test-service test-service-full test-service-unit test-service-integration test-service-e2e test-user test-gateway test-restaurant test-order test-payment test-delivery test-user-unit test-gateway-unit test-restaurant-unit test-order-unit test-payment-unit test-delivery-unit test-user-integration test-gateway-integration test-restaurant-integration test-order-integration test-payment-integration test-delivery-integration test-user-e2e test-gateway-e2e test-restaurant-e2e test-order-e2e test-payment-e2e test-delivery-e2e lint format type-check pre-commit migrate seed dev-payment dev-delivery

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; elif docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)
COMPOSE := $(DOCKER_COMPOSE) --env-file .env -f infrastructure/docker-compose.yml
COMPOSE_TEST := $(COMPOSE) --profile test
WAIT_HTTP_RETRIES ?= 45
WAIT_HTTP_SLEEP_SECONDS ?= 1
TEST_STACK_SERVICES := postgres redis user-service restaurant-service payment-service delivery-service order-service
E2E_STACK_SERVICES := $(TEST_STACK_SERVICES) api-gateway

help: ## Show this help message
	@echo "$(BLUE)Food Delivery - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

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

docker-ready: ## Fail fast if Docker daemon is unavailable
	@docker info >/dev/null 2>&1 || (echo "$(RED)Docker daemon is not running. Start Docker Desktop/daemon and retry.$(NC)"; exit 1)

up: ## Start all services (docker-compose up -d)
	@$(MAKE) docker-ready
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
	@for i in $$(seq 1 $(WAIT_HTTP_RETRIES)); do \
		if curl -fsS "$(URL)" >/dev/null 2>&1; then \
			exit 0; \
		fi; \
		sleep $(WAIT_HTTP_SLEEP_SECONDS); \
	done; \
	echo "$(RED)Timeout waiting for $(URL) after $(WAIT_HTTP_RETRIES)s$(NC)"; \
	exit 1

test: ## Run repo-level tests from ./tests only
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if find tests -type f -name "test_*.py" 2>/dev/null | grep -q .; then \
			/opt/venv/bin/pytest; \
		else \
			echo "No root tests found in ./tests; skipping."; \
		fi'

test-deps-up: ## Start integration test dependencies and wait until healthy
	@$(MAKE) docker-ready
	@$(COMPOSE) up -d $(TEST_STACK_SERVICES)
	@$(MAKE) wait-http URL=http://localhost:8001/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8002/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8003/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8004/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8005/health WAIT_HTTP_RETRIES=30

test-e2e-deps-up: ## Start e2e test dependencies and wait until healthy
	@$(MAKE) docker-ready
	@$(COMPOSE) up -d $(E2E_STACK_SERVICES)
	@$(MAKE) wait-http URL=http://localhost:8000/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8001/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8002/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8003/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8004/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8005/health WAIT_HTTP_RETRIES=30

test-all: ## Run repo + all services (unit + integration, excludes e2e)
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running all tests in Docker...$(NC)"
	@$(MAKE) test-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if find tests -type f -name "test_*.py" 2>/dev/null | grep -q .; then \
			echo "Running repo tests in ./tests..."; \
			/opt/venv/bin/pytest; \
		else \
			echo "No root tests found in ./tests; skipping."; \
		fi; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				paths=""; \
				if [ -d "$$svc/tests/unit" ]; then paths="$$paths tests/unit"; fi; \
				if [ -d "$$svc/tests/integration" ]; then paths="$$paths tests/integration"; fi; \
				if [ -n "$$paths" ]; then \
					echo "Running unit+integration tests in $$svc..."; \
					(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml $$paths); \
				else \
					echo "No unit/integration tests in $$svc; skipping."; \
				fi; \
			fi; \
		done'

test-all-full: ## Run repo + all services (unit + integration + e2e)
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running full test matrix in Docker (including e2e)...$(NC)"
	@$(MAKE) test-e2e-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if find tests -type f -name "test_*.py" 2>/dev/null | grep -q .; then \
			echo "Running repo tests in ./tests..."; \
			/opt/venv/bin/pytest; \
		else \
			echo "No root tests found in ./tests; skipping."; \
		fi; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				if [ -d "$$svc/tests" ]; then \
					echo "Running all tests in $$svc..."; \
					(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml tests); \
				else \
					echo "No tests directory in $$svc; skipping."; \
				fi; \
			fi; \
		done'

test-unit: ## Run unit tests for all services
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running unit tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if [ -d tests/unit ]; then \
			echo "Running repo unit tests in ./tests/unit..."; \
			/opt/venv/bin/pytest tests/unit; \
		else \
			echo "No repo unit tests found in ./tests/unit; skipping."; \
		fi; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				if [ -d "$$svc/tests/unit" ]; then \
					echo "Running unit tests in $$svc..."; \
					(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml tests/unit); \
				else \
					echo "No unit tests in $$svc; skipping."; \
				fi; \
			fi; \
		done'

test-integration: ## Run integration tests for all services
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running integration tests in Docker...$(NC)"
	@$(MAKE) test-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if [ -d tests/integration ]; then \
			echo "Running repo integration tests in ./tests/integration..."; \
			/opt/venv/bin/pytest tests/integration; \
		else \
			echo "No repo integration tests found in ./tests/integration; skipping."; \
		fi; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				if [ -d "$$svc/tests/integration" ]; then \
					echo "Running integration tests in $$svc..."; \
					(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml tests/integration); \
				else \
					echo "No integration tests in $$svc; skipping."; \
				fi; \
			fi; \
		done'

test-e2e: ## Run end-to-end tests for all services
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running E2E tests in Docker...$(NC)"
	@$(MAKE) test-e2e-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		if [ -d tests/e2e ]; then \
			echo "Running repo e2e tests in ./tests/e2e..."; \
			/opt/venv/bin/pytest tests/e2e; \
		else \
			echo "No repo e2e tests found in ./tests/e2e; skipping."; \
		fi; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				if [ -d "$$svc/tests/e2e" ]; then \
					echo "Running E2E tests in $$svc..."; \
					(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml tests/e2e); \
				else \
					echo "No e2e tests in $$svc; skipping."; \
				fi; \
			fi; \
		done'

test-cov: ## Run tests with coverage report
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running tests with coverage in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm test-runner bash -lc 'set -e; \
		for svc in services/*; do \
			if [ -d "$$svc" ]; then \
				echo "Running coverage in $$svc..."; \
				(cd "$$svc" && /opt/venv/bin/pytest -c pyproject.toml); \
			fi; \
		done'

test-service-prepare: ## Start required dependencies for SERVICE integration/e2e tests
	@$(MAKE) docker-ready
ifdef SERVICE
	@case "$(SERVICE)" in \
		api-gateway) \
			$(COMPOSE) up -d postgres redis user-service order-service; \
			$(MAKE) wait-http URL=http://localhost:8001/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8003/health WAIT_HTTP_RETRIES=30; \
			;; \
		order-service) \
			$(COMPOSE) up -d postgres redis restaurant-service payment-service delivery-service; \
			$(MAKE) wait-http URL=http://localhost:8002/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8004/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8005/health WAIT_HTTP_RETRIES=30; \
			;; \
		user-service|restaurant-service) \
			$(COMPOSE) up -d postgres redis; \
			;; \
		payment-service|delivery-service) \
			;; \
		*) \
			echo "$(RED)Error: Unknown service '$(SERVICE)'$(NC)"; \
			exit 1; \
			;; \
	esac
else
	@echo "$(RED)Error: Please specify SERVICE=name (e.g. SERVICE=user-service)$(NC)"
	@exit 1
endif

test-service: ## Run unit + integration tests for SERVICE (excludes e2e)
	@echo "$(BLUE)Running service unit+integration tests in Docker...$(NC)"
	@$(MAKE) test-service-prepare SERVICE=$(SERVICE)
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		cd services/$(SERVICE); \
		paths=""; \
		if [ -d tests/unit ]; then paths="$$paths tests/unit"; fi; \
		if [ -d tests/integration ]; then paths="$$paths tests/integration"; fi; \
		if [ -n "$$paths" ]; then \
			/opt/venv/bin/pytest -c pyproject.toml $$paths; \
		else \
			echo "No unit/integration tests for $(SERVICE); skipping."; \
		fi'

test-service-full: ## Run all tests for a specific service (including e2e)
	@echo "$(BLUE)Running full service test matrix in Docker...$(NC)"
	@$(MAKE) test-service-prepare SERVICE=$(SERVICE)
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		cd services/$(SERVICE); \
		if [ -d tests ]; then \
			/opt/venv/bin/pytest -c pyproject.toml tests; \
		else \
			echo "No tests directory for $(SERVICE); skipping."; \
		fi'

test-service-unit: ## Run unit tests for a specific service (SERVICE=name)
	@$(MAKE) docker-ready
ifdef SERVICE
	$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		cd services/$(SERVICE); \
		if [ -d tests/unit ]; then \
			/opt/venv/bin/pytest -c pyproject.toml tests/unit; \
		else \
			echo "No unit tests for $(SERVICE); skipping."; \
		fi'
else
	@echo "$(RED)Error: Please specify SERVICE=name (e.g. SERVICE=user-service)$(NC)"
	@exit 1
endif

test-service-integration: ## Run integration tests for a specific service (SERVICE=name)
	@$(MAKE) test-service-prepare SERVICE=$(SERVICE)
ifdef SERVICE
	$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		cd services/$(SERVICE); \
		if [ -d tests/integration ]; then \
			/opt/venv/bin/pytest -c pyproject.toml tests/integration; \
		else \
			echo "No integration tests for $(SERVICE); skipping."; \
		fi'
else
	@echo "$(RED)Error: Please specify SERVICE=name (e.g. SERVICE=user-service)$(NC)"
	@exit 1
endif

test-service-e2e: ## Run e2e tests for a specific service (SERVICE=name)
	@$(MAKE) test-service-prepare SERVICE=$(SERVICE)
ifdef SERVICE
	$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		cd services/$(SERVICE); \
		if [ -d tests/e2e ]; then \
			/opt/venv/bin/pytest -c pyproject.toml tests/e2e; \
		else \
			echo "No e2e tests for $(SERVICE); skipping."; \
		fi'
else
	@echo "$(RED)Error: Please specify SERVICE=name (e.g. SERVICE=user-service)$(NC)"
	@exit 1
endif

test-user: ## Run tests for user service
	@$(MAKE) test-service SERVICE=user-service

test-gateway: ## Run tests for API Gateway
	@$(MAKE) test-service SERVICE=api-gateway

test-restaurant: ## Run tests for restaurant service
	@$(MAKE) test-service SERVICE=restaurant-service

test-order: ## Run tests for order service
	@$(MAKE) test-service SERVICE=order-service

test-payment: ## Run tests for payment service
	@$(MAKE) test-service SERVICE=payment-service

test-delivery: ## Run tests for delivery service
	@$(MAKE) test-service SERVICE=delivery-service

test-user-unit: ## Run unit tests for user service
	@$(MAKE) test-service-unit SERVICE=user-service

test-gateway-unit: ## Run unit tests for API Gateway
	@$(MAKE) test-service-unit SERVICE=api-gateway

test-restaurant-unit: ## Run unit tests for restaurant service
	@$(MAKE) test-service-unit SERVICE=restaurant-service

test-order-unit: ## Run unit tests for order service
	@$(MAKE) test-service-unit SERVICE=order-service

test-payment-unit: ## Run unit tests for payment service
	@$(MAKE) test-service-unit SERVICE=payment-service

test-delivery-unit: ## Run unit tests for delivery service
	@$(MAKE) test-service-unit SERVICE=delivery-service

test-user-integration: ## Run integration tests for user service
	@$(MAKE) test-service-integration SERVICE=user-service

test-gateway-integration: ## Run integration tests for API Gateway
	@$(MAKE) test-service-integration SERVICE=api-gateway

test-restaurant-integration: ## Run integration tests for restaurant service
	@$(MAKE) test-service-integration SERVICE=restaurant-service

test-order-integration: ## Run integration tests for order service
	@$(MAKE) test-service-integration SERVICE=order-service

test-payment-integration: ## Run integration tests for payment service
	@$(MAKE) test-service-integration SERVICE=payment-service

test-delivery-integration: ## Run integration tests for delivery service
	@$(MAKE) test-service-integration SERVICE=delivery-service

test-user-e2e: ## Run e2e tests for user service
	@$(MAKE) test-service-e2e SERVICE=user-service

test-gateway-e2e: ## Run e2e tests for API Gateway
	@$(MAKE) test-service-e2e SERVICE=api-gateway

test-restaurant-e2e: ## Run e2e tests for restaurant service
	@$(MAKE) test-service-e2e SERVICE=restaurant-service

test-order-e2e: ## Run e2e tests for order service
	@$(MAKE) test-service-e2e SERVICE=order-service

test-payment-e2e: ## Run e2e tests for payment service
	@$(MAKE) test-service-e2e SERVICE=payment-service

test-delivery-e2e: ## Run e2e tests for delivery service
	@$(MAKE) test-service-e2e SERVICE=delivery-service

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
	MYPYPATH=shared/src:services/payment-service mypy services/payment-service/src
	MYPYPATH=shared/src:services/delivery-service mypy services/delivery-service/src
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

dev-payment: ## Run Payment Service locally
	@echo "$(BLUE)Starting Payment Service...$(NC)"
	cd services/payment-service && uvicorn src.main:app --reload --port 8004

dev-delivery: ## Run Delivery Service locally
	@echo "$(BLUE)Starting Delivery Service...$(NC)"
	cd services/delivery-service && uvicorn src.main:app --reload --port 8005

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
