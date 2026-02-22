# Restaurant Service

Restaurant and menu management service for the Food Delivery platform.

## Overview

The Restaurant Service manages:
- Restaurant creation and updates (by restaurant owners)
- Menu management (add/update/delete menu items)
- Restaurant search and discovery
- Menu item availability tracking

## Architecture

This service follows **Clean Architecture** pattern:

```
src/
├── domain/              # Business logic (entities, value objects, exceptions)
├── application/         # Use cases and DTOs
├── infrastructure/      # Database, caching, external services
└── interface/           # HTTP API (FastAPI routes)
```

## API Endpoints

### Restaurant Management (Restaurant Owner only)
- `POST /api/v1/restaurants` - Create restaurant
- `PUT /api/v1/restaurants/{id}` - Update restaurant
- `DELETE /api/v1/restaurants/{id}` - Deactivate restaurant

### Restaurant Discovery (Public)
- `GET /api/v1/restaurants` - Search/list restaurants
- `GET /api/v1/restaurants/{id}` - Get single restaurant
- `GET /api/v1/restaurants/{id}/menu` - Get restaurant menu

### Menu Management (Owner only)
- `POST /api/v1/restaurants/{id}/menu-items` - Add menu item
- `GET /api/v1/restaurants/{id}/menu-items/{item_id}` - Get menu item
- `PUT /api/v1/restaurants/{id}/menu-items/{item_id}` - Update menu item
- `PATCH /api/v1/restaurants/{id}/menu-items/{item_id}/availability` - Toggle availability
- `DELETE /api/v1/restaurants/{id}/menu-items/{item_id}` - Delete menu item

## Configuration

Environment variables (prefix: `RESTAURANT_SERVICE_`):

- `RESTAURANT_SERVICE_DB_NAME` - Database name
- `RESTAURANT_SERVICE_DB_USER` - Database user
- `RESTAURANT_SERVICE_DB_PASSWORD` - Database password
- `RESTAURANT_SERVICE_KAFKA_ENABLED` - Enable Kafka event publishing (`true/false`)
- `RESTAURANT_SERVICE_REDIS_HOST` - Redis host (for caching)
- `RESTAURANT_SERVICE_REDIS_PORT` - Redis port
- `RESTAURANT_SERVICE_REDIS_DB` - Redis database number

Shared Kafka settings:
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker endpoints (for example, `localhost:9093`)

## Development

```bash
# Install dependencies
cd services/restaurant-service
uv sync --all-extras

# Run locally (hot reload)
make dev-restaurant

# Run tests
make test-restaurant

# Run migrations
cd services/restaurant-service
alembic upgrade head
```

## Testing

```bash
# Unit tests
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# With coverage
pytest --cov=src --cov-report=html
```

## Documentation

- [ADR-003: Restaurant Service Architecture](../../docs/adr/003-restaurant-service-architecture.md)
- [API Conventions](../../docs/API_CONVENTIONS.md)
- [Engineering Conventions](../../docs/ENGINEERING_CONVENTIONS.md)
