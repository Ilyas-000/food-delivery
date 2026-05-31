# ADR-001: Microservices Architecture Baseline

**Status**: Accepted
**Date**: 2026-05-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

The project models a food delivery backend with independently owned domains: users, restaurants, orders, payments, delivery, notifications, analytics and reviews. The repository is a monorepo, but runtime services have separate processes, ports, settings, tests and storage boundaries.

The architecture needs to make service ownership explicit while keeping local development practical.

## Decision

The platform uses FastAPI microservices behind a single API Gateway:

- API Gateway owns external routing, JWT validation, rate limiting, circuit breaker behavior and WebSocket proxying.
- Domain services own their HTTP contracts and application logic.
- Internal orchestration calls use direct service-to-service HTTP.
- Kafka is used for domain and operational events.
- Redis is used for short-lived coordination concerns: refresh tokens, rate limiting and delivery tracking fanout.
- PostgreSQL stores service-owned transactional data.
- ClickHouse stores analytics read data.
- `shared/` contains cross-service contracts and infrastructure helpers, but not domain logic.

## Consequences

### Positive

- Service boundaries match business capabilities.
- Gateway concerns do not leak into domain services.
- Services can be tested and run individually.
- The monorepo keeps shared contracts and local tooling simple.

### Negative

- Local startup has more infrastructure than a modular monolith.
- Cross-service flows need explicit failure handling.
- Data joins across services cannot rely on database joins.

### Risks

- Service boundaries can drift if shared code starts containing business logic.
- Synchronous internal HTTP chains increase latency on write flows.
- Eventual consistency must be handled explicitly where events are used.

## Alternatives Considered

### Modular monolith

**Pros**:
- Simpler deployment and local runtime.
- Easier transactional consistency.

**Cons**:
- Less realistic service-boundary practice.
- Harder to isolate infrastructure and ownership concerns per domain.

**Why rejected**: the project is intended to exercise service boundaries, gateway concerns, eventing and independent persistence.

### Fully event-driven command processing

**Pros**:
- Lower coupling between write paths.
- Easier async workflow scaling after acceptance.

**Cons**:
- More complex client contracts and recovery semantics.
- Harder to debug while domain services are still evolving.

**Why rejected**: direct HTTP contracts are clearer for the current order creation and validation flow.

## Implementation Notes

- Services live under `services/*`.
- Shared contracts and helpers live under `shared/src/shared`.
- Runtime composition is described in `infrastructure/docker-compose.yml`.
- API routes are proxied by `services/api-gateway/src/routes/proxy.py`.

## References

- [006-clean-architecture-conventions.md](006-clean-architecture-conventions.md)
- [008-postgresql-database-per-service.md](008-postgresql-database-per-service.md)
