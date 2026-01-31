# CLAUDE.md

This file provides guidance for AI agents working in this repository.

## Project Overview

Food Delivery is a microservice-based platform. Currently implemented services:
- API Gateway (routing, JWT validation, rate limiting, circuit breaker)
- User Service (registration, login, profile)

Other services are planned and tracked in `DEVELOPMENT-ROADMAP.md` and `PROGRESS.md`.

## Tech Stack

- Python 3.12 + FastAPI
- PostgreSQL 15
- Redis 7
- Kafka
- Docker & Docker Compose

## Architecture Rules

- Domain is pure (no framework/infrastructure dependencies).
- Application depends on Domain only.
- Infrastructure implements Application interfaces.
- Interface depends on Application.
- Config comes from settings, no hardcoded host/ports.

## Development Commands

### Infrastructure
```bash
make setup-dev
make up
make down
make logs
make health
```

### Local Development
```bash
make dev-user
make dev-gateway
```

### Testing
```bash
make test
make test-all
make test-user
make test-gateway
make test-cov
```

## Key Patterns

- Clean Architecture per service
- API Gateway pattern
- Circuit breaker for backend protection
- Rate limiting with Redis

## Important Files

- `docs/API_CONVENTIONS.md`
- `docs/ENGINEERING_CONVENTIONS.md`
- `docs/TECH_DEBT.md`
- `docs/adr/`
- `DEVELOPMENT-ROADMAP.md`
- `PROGRESS.md`
