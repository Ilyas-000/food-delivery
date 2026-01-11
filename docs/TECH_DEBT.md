# Technical Debt

This file tracks agreed technical debt items for later cleanup.

## Backlog

- Naming consistency: simplify and clarify naming (DTO/use_case, module names, route names).
- Over-commented code: reduce boilerplate/explanatory comments, keep only non-obvious logic notes.
- API responses metadata: large inline `responses` blocks in routes should be simplified or moved.
- Infrastructure startup reliability: `depends_on: condition: service_healthy` was removed for `user-service` and `api-gateway` in `infrastructure/docker-compose.yml` to avoid first-run failures; consider reintroducing via a dev override or robust wait-for logic.
- User Service log level normalization: `services/user-service/docker-entrypoint.sh` lowercases `USER_SERVICE_LOG_LEVEL` as a workaround for uvicorn’s strict enum; move normalization to config or unify env values.
- Postgres privileges: `infrastructure/postgres/init-databases.sh` grants on schema `public` were added only for `user-service`; generalize role/privilege creation for all services and ensure `.env.example` includes `*_DB_USER` and `*_DB_PASSWORD`.
- Health checks: `scripts/check-health.sh` verifies only infrastructure services; add `user-service` and `api-gateway` checks to avoid false green status.
- Docker Compose warning: remove obsolete `version` key in `infrastructure/docker-compose.yml` to reduce startup noise.
- Clean targets: `make clean` now removes local images (`--rmi local`) to avoid stale builds; consider splitting into `clean` vs `clean-images` to reduce accidental image loss.
- API Gateway tests: integration suite relies on heavy mocking but uses `integration` mark; consider reclassifying to unit tests or running against real Redis/User Service.
- API Gateway tests: route expectations are stale (`/api/v1/users/profile` vs `/api/v1/users/me`) and should match current gateway routes.
- API Gateway tests: response assertions expect `"detail"` strings, but gateway returns `{ "error": { "code", "message" } }` payloads.
- API Gateway tests: `httpx.AsyncClient` mocks return empty `content` so proxy responses lose JSON; mocks should set `response.content` to serialized JSON bytes.
- API Gateway tests: env vars in `tests/conftest.py` use wrong names (`USER_SERVICE_URL`, `REDIS_HOST/PORT`), but gateway config reads `GATEWAY_USER_SERVICE_URL` and `GATEWAY_REDIS_*`.
- API Gateway tests: circuit breaker tests use a test app without the circuit breaker middleware, so they do not exercise CB behavior.
- Env config mismatch: root `.env` uses `API_GATEWAY_*`, while gateway settings expect `GATEWAY_*`; align names or add explicit aliases so local runs behave like Docker.
- Env config mismatch: gateway settings read `JWT_SECRET_KEY/JWT_ALGORITHM`, but Docker injects `GATEWAY_JWT_*`; ensure a single source of truth and consistent names across `.env`, compose, and service config.
- Env config mismatch: user-service local config reads `USER_SERVICE_JWT_*`, but root `.env` only defines `JWT_*`; local run without compose will miss JWT settings unless mapped.
- Env config mismatch: gateway settings use `env_file=".env"` (service-local), while user-service uses `env_file="../../.env"` (repo root); standardize or document expected run location.
