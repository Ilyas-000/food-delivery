.PHONY: help install dev-install up down restart logs health clean test lint format type-check pre-commit migrate seed

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

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
	uv sync --frozen --all-extras
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)Development environment ready!$(NC)"

## Docker & Services

up: ## Start all services (docker-compose up -d)
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose --env-file .env -f infrastructure/docker-compose.yml up -d
	@echo "$(GREEN)All services started!$(NC)"
	@$(MAKE) health

down: ## Stop all services (docker-compose down)
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose --env-file .env -f infrastructure/docker-compose.yml down

restart: ## Restart all services
	@$(MAKE) down
	@$(MAKE) up

logs: ## Show logs from all services (use SERVICE=name for specific service)
	@echo "$(BLUE)Showing logs...$(NC)"
ifdef SERVICE
	docker-compose --env-file .env -f infrastructure/docker-compose.yml logs -f $(SERVICE)
else
	docker-compose --env-file .env -f infrastructure/docker-compose.yml logs -f
endif

health: ## Check health of all services
	@echo "$(BLUE)Checking services health...$(NC)"
	@bash scripts/check-health.sh

clean: ## Remove all containers, volumes, and build artifacts
	@echo "$(RED)Cleaning up...$(NC)"
	docker-compose --env-file .env -f infrastructure/docker-compose.yml down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

## Testing & Quality

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -m integration

test-e2e: ## Run end-to-end tests only
	@echo "$(BLUE)Running E2E tests...$(NC)"
	pytest -m e2e

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

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
	mypy services/ shared/

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

dev-restaurant: ## Run Restaurant Service locally
	@echo "$(BLUE)Starting Restaurant Service...$(NC)"
	cd services/restaurant-service && uvicorn src.main:app --reload --port 8002

dev-order: ## Run Order Service locally
	@echo "$(BLUE)Starting Order Service...$(NC)"
	cd services/order-service && uvicorn src.main:app --reload --port 8003

dev-gateway: ## Run API Gateway locally
	@echo "$(BLUE)Starting API Gateway...$(NC)"
	cd services/api-gateway && uvicorn src.main:app --reload --port 8000

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
	docker-compose --env-file .env -f infrastructure/docker-compose.yml ps
