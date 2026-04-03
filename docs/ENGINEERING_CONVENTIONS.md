# Engineering Conventions

This document captures the agreed engineering rules and style for the project.
When code changes, keep this file in sync.

## Architecture Boundaries

- Domain is pure: no framework or infrastructure dependencies.
- Application depends on Domain only.
- Infrastructure implements Application interfaces.
- Interface (API, Kafka consumers) depends on Application.
- Never import SQLAlchemy (or any infrastructure) inside application or domain.

## Communication Boundaries

- External (north-south) traffic goes through API Gateway only.
- Internal service-to-service (east-west) traffic is direct between services, not через gateway.
- Saga HTTP steps (for example `order-service -> payment-service/delivery-service`) are internal contracts.
- Kafka is the default transport for durable inter-service domain events.
- Redis Pub/Sub is for low-latency ephemeral fanout (for example delivery WebSocket updates), not a replacement for durable event integration.

## Data Modeling & Validation

- Domain uses plain classes/dataclasses and Value Objects for business rules.
- Application DTOs are Pydantic models (BaseModel) for internal data transfer.
- API schemas are Pydantic models with minimal type parsing only.
- Business validation lives in Domain (single source of truth).
- Use `Annotated` for validation constraints in Pydantic models.
- Use `Field` only when needed (default_factory, explicit schema behavior).
- Avoid verbose `Field` examples in code; keep examples in docs when needed.

## Errors & HTTP Responses

- Error format must follow `docs/API_CONVENTIONS.md`.
- Domain exceptions map to HTTP responses in interface layer handlers.
- Use 422 for domain validation errors unless API conventions say otherwise.

## Configuration & Environment

- Service settings use `USER_SERVICE_` (or service-specific prefix).
- Shared PostgreSQL settings use `POSTGRES_*`.
- Service-specific DB overrides: `SERVICE_DB_NAME/USER/PASSWORD`.
- Avoid `*_DATABASE_URL` and hardcoded host/port in code.
- All runtime config should come from settings.
- Prefer a single root `.env` for local dev; avoid per-service `.env` files.

## Logging & Tracing

- Use `structlog` consistently across services.
- Log at API boundaries (request-level) and key business events only.
- Prefer structured fields (service, request_id, user_id) over free-form text.

## Kafka & Events

- Topic naming: `{service}.{entity}.{action}`.
- `event_type` must match the Kafka topic exactly.
- Event contracts live in `shared/src/shared/events`.

## Health Endpoints

- Provide `/health` for liveness.
- `/ready` is optional; include only if readiness checks differ from liveness.

## Testing

- Service tests should enable the shared pytest summary plugin:
  `pytest_plugins = ["shared.testing.pytest_summary"]` in `conftest.py`.

## Quick Fixes

- If a change is a temporary workaround, call it out explicitly and record it in `docs/TECH_DEBT.md`.
