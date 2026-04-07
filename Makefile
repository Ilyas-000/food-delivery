.PHONY: help install dev-install setup-dev docker-ready up down restart logs health clean clean-image clean-images test test-all test-all-full test-unit test-integration test-e2e test-e2e-load test-cov test-deps-up test-e2e-deps-up test-service-prepare test-service test-service-full test-service-unit test-service-integration test-service-e2e test-user test-gateway test-restaurant test-order test-payment test-delivery test-notification test-analytics test-review test-user-unit test-gateway-unit test-restaurant-unit test-order-unit test-payment-unit test-delivery-unit test-notification-unit test-analytics-unit test-review-unit test-user-integration test-gateway-integration test-restaurant-integration test-order-integration test-payment-integration test-delivery-integration test-notification-integration test-analytics-integration test-review-integration test-user-e2e test-gateway-e2e test-restaurant-e2e test-order-e2e test-payment-e2e test-delivery-e2e test-notification-e2e test-analytics-e2e test-review-e2e lint format type-check pre-commit migrate seed dev-payment dev-delivery dev-notification dev-analytics dev-review

# Default target
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

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
TEST_STACK_SERVICES := postgres redis user-service restaurant-service payment-service delivery-service order-service review-service
E2E_STACK_SERVICES := $(TEST_STACK_SERVICES) kafka clickhouse notification-service analytics-service api-gateway

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
		fi'

test-deps-up: ## Start integration test dependencies and wait until healthy
	@$(MAKE) docker-ready
	@$(COMPOSE) up -d --force-recreate $(TEST_STACK_SERVICES)
	@bash scripts/bootstrap-test-databases.sh
	@$(MAKE) wait-http URL=http://localhost:8001/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8002/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8003/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8004/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8005/health WAIT_HTTP_RETRIES=30
	@$(MAKE) wait-http URL=http://localhost:8008/health WAIT_HTTP_RETRIES=30

test-e2e-deps-up: ## Start e2e test dependencies and wait until healthy
	@$(MAKE) docker-ready
	@$(COMPOSE) up -d --force-recreate $(E2E_STACK_SERVICES)
	@bash infrastructure/kafka/create-topics.sh
	@bash scripts/bootstrap-test-databases.sh
	@$(MAKE) wait-http URL=http://localhost:8000/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8001/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8002/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8003/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8004/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8005/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8006/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8123/ping WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8007/health WAIT_HTTP_RETRIES=60
	@$(MAKE) wait-http URL=http://localhost:8008/health WAIT_HTTP_RETRIES=60

test-all: ## Run repo + all services (unit + integration, excludes e2e)
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running all tests in Docker...$(NC)"
	@$(MAKE) test-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc './scripts/run-test-matrix.sh unit+integration'

test-all-full: ## Run repo + all services (unit + integration + e2e)
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running full test matrix in Docker (including e2e)...$(NC)"
	@$(MAKE) test-e2e-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc './scripts/run-test-matrix.sh all'

test-unit: ## Run unit tests for all services
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running unit tests in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc './scripts/run-test-matrix.sh unit'

test-integration: ## Run integration tests for all services
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running integration tests in Docker...$(NC)"
	@$(MAKE) test-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc './scripts/run-test-matrix.sh integration'

test-e2e: ## Run end-to-end tests for all services
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running E2E tests in Docker...$(NC)"
	@$(MAKE) test-e2e-deps-up
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc './scripts/run-test-matrix.sh e2e'

test-e2e-load: ## Run opt-in repo-level load smoke for concurrent order creation
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running E2E load smoke in Docker...$(NC)"
	@$(MAKE) test-e2e-deps-up
	@printf "\n$(BLUE)============================================================$(NC)\n"
	@printf "$(BLUE)==  %s | %s$(NC)\n" "REPO" "e2e-load"
	@printf "$(BLUE)============================================================$(NC)\n\n"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
		RUN_E2E_LOAD=1 E2E_CONCURRENT_ORDERS=$${E2E_CONCURRENT_ORDERS:-10} /opt/venv/bin/pytest tests/e2e/test_order_journey.py -c pyproject.toml -m "e2e and slow"'

test-cov: ## Run tests with coverage report
	@$(MAKE) docker-ready
	@echo "$(BLUE)Running tests with coverage in Docker...$(NC)"
	@$(COMPOSE_TEST) run --rm test-runner bash -lc './scripts/run-test-matrix.sh coverage'

test-service-prepare: ## Start required dependencies for SERVICE integration/e2e tests
	@$(MAKE) docker-ready
ifdef SERVICE
	@case "$(SERVICE)" in \
		api-gateway) \
			$(COMPOSE) up -d postgres redis user-service order-service kafka clickhouse analytics-service review-service; \
			bash scripts/bootstrap-test-databases.sh; \
			$(MAKE) wait-http URL=http://localhost:8001/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8003/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8123/ping WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8007/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8008/health WAIT_HTTP_RETRIES=30; \
			;; \
		order-service) \
			$(COMPOSE) up -d postgres redis restaurant-service payment-service delivery-service; \
			bash scripts/bootstrap-test-databases.sh; \
			$(MAKE) wait-http URL=http://localhost:8002/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8004/health WAIT_HTTP_RETRIES=30; \
			$(MAKE) wait-http URL=http://localhost:8005/health WAIT_HTTP_RETRIES=30; \
			;; \
		user-service|restaurant-service|review-service) \
			$(COMPOSE) up -d postgres redis; \
			bash scripts/bootstrap-test-databases.sh; \
			;; \
		payment-service|delivery-service|notification-service) \
			;; \
		analytics-service) \
			$(COMPOSE) up -d kafka clickhouse; \
			$(MAKE) wait-http URL=http://localhost:8123/ping WAIT_HTTP_RETRIES=30; \
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
	@printf "\n$(BLUE)============================================================$(NC)\n"
	@printf "$(BLUE)==  %s | %s$(NC)\n" "$(SERVICE)" "unit+integration"
	@printf "$(BLUE)============================================================$(NC)\n\n"
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
	@printf "\n$(BLUE)============================================================$(NC)\n"
	@printf "$(BLUE)==  %s | %s$(NC)\n" "$(SERVICE)" "full test matrix"
	@printf "$(BLUE)============================================================$(NC)\n\n"
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
	@printf "\n$(BLUE)============================================================$(NC)\n"
	@printf "$(BLUE)==  %s | %s$(NC)\n" "$(SERVICE)" "unit"
	@printf "$(BLUE)============================================================$(NC)\n\n"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
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
	@printf "\n$(BLUE)============================================================$(NC)\n"
	@printf "$(BLUE)==  %s | %s$(NC)\n" "$(SERVICE)" "integration"
	@printf "$(BLUE)============================================================$(NC)\n\n"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
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
	@printf "\n$(BLUE)============================================================$(NC)\n"
	@printf "$(BLUE)==  %s | %s$(NC)\n" "$(SERVICE)" "e2e"
	@printf "$(BLUE)============================================================$(NC)\n\n"
	@$(COMPOSE_TEST) run --rm --no-deps test-runner bash -lc 'set -e; \
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

test-notification: ## Run tests for notification service
	@$(MAKE) test-service SERVICE=notification-service

test-analytics: ## Run tests for analytics service
	@$(MAKE) test-service SERVICE=analytics-service

test-review: ## Run tests for review service
	@$(MAKE) test-service SERVICE=review-service

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

test-notification-unit: ## Run unit tests for notification service
	@$(MAKE) test-service-unit SERVICE=notification-service

test-analytics-unit: ## Run unit tests for analytics service
	@$(MAKE) test-service-unit SERVICE=analytics-service

test-review-unit: ## Run unit tests for review service
	@$(MAKE) test-service-unit SERVICE=review-service

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

test-notification-integration: ## Run integration tests for notification service
	@$(MAKE) test-service-integration SERVICE=notification-service

test-analytics-integration: ## Run integration tests for analytics service
	@$(MAKE) test-service-integration SERVICE=analytics-service

test-review-integration: ## Run integration tests for review service
	@$(MAKE) test-service-integration SERVICE=review-service

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

test-notification-e2e: ## Run e2e tests for notification service
	@$(MAKE) test-service-e2e SERVICE=notification-service

test-analytics-e2e: ## Run e2e tests for analytics service
	@$(MAKE) test-service-e2e SERVICE=analytics-service

test-review-e2e: ## Run e2e tests for review service
	@$(MAKE) test-service-e2e SERVICE=review-service

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
	MYPYPATH=shared/src:services/notification-service mypy services/notification-service/src
	MYPYPATH=shared/src:services/analytics-service mypy services/analytics-service/src
	MYPYPATH=shared/src:services/review-service mypy services/review-service/src
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

dev-notification: ## Run Notification Service locally
	@echo "$(BLUE)Starting Notification Service...$(NC)"
	cd services/notification-service && uvicorn src.main:app --reload --port 8006

dev-analytics: ## Run Analytics Service locally
	@echo "$(BLUE)Starting Analytics Service...$(NC)"
	cd services/analytics-service && uvicorn src.main:app --reload --port 8007

dev-review: ## Run Review Service locally
	@echo "$(BLUE)Starting Review Service...$(NC)"
	cd services/review-service && uvicorn src.main:app --reload --port 8008

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
