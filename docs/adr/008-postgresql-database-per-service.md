# ADR-008: PostgreSQL Database-per-Service Strategy

**Status**: Accepted
**Date**: 2026-05-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

Several services need transactional state: users, restaurants, orders and reviews. The project uses one PostgreSQL server in local infrastructure, but service ownership still needs to be separated.

The design must avoid cross-service schema coupling and still keep local setup manageable.

## Decision

Use database-per-service on PostgreSQL:
- each stateful service gets its own database and database user;
- each service owns its Alembic migrations;
- service schemas do not define foreign keys to other service databases;
- cross-service references are stored as external ids and validated through service contracts;
- integration tests use isolated test databases where available.

The local Docker Compose stack uses one PostgreSQL container with multiple logical databases.

## Consequences

### Positive

- Service data ownership is explicit.
- Migrations can evolve per service.
- Direct database joins cannot accidentally couple services.
- Local development remains lighter than one PostgreSQL container per service.

### Negative

- Cross-service consistency must be handled through APIs, saga compensation and events.
- Reporting needs read models such as Analytics Service and ClickHouse.
- Local bootstrap must create several databases and roles.

### Risks

- Reused local PostgreSQL volumes can miss new databases because init scripts run only on first volume creation.
- External ids can become stale if the owning service deletes or changes data.
- Lack of database foreign keys requires application-level validation.

## Alternatives Considered

### Single shared database and schema

**Pros**:
- Simple joins and constraints.
- Easier initial setup.

**Cons**:
- Tight coupling between services.
- Schema changes in one service can break others.
- Service ownership becomes unclear.

**Why rejected**: the project needs independent service data boundaries.

### Separate PostgreSQL server per service

**Pros**:
- Stronger operational isolation.
- Independent tuning and scaling.

**Cons**:
- Heavier local runtime.
- More Compose and bootstrap overhead.

**Why rejected**: separate logical databases provide enough separation for this repository while keeping local runtime practical.

## Implementation Notes

- Bootstrap script: `infrastructure/postgres/init-databases.sh`
- Runtime composition: `infrastructure/docker-compose.yml`
- Alembic directories live inside the owning service.
- Integration test bootstrap: `scripts/bootstrap-test-databases.sh`

## References

- [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md)
- [006-clean-architecture-conventions.md](006-clean-architecture-conventions.md)
