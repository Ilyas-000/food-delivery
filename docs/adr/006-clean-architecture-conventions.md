# ADR-006: Clean Architecture Conventions Across Services

**Status**: Accepted
**Date**: 2026-05-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

The services share the same technical stack, but each domain has different business rules and infrastructure needs. A consistent structure is needed so use cases remain testable and infrastructure changes do not leak into domain code.

## Decision

Domain services use the same layer layout:

```text
src/
├── domain/
├── application/
├── infrastructure/
└── interface/
```

Layer responsibilities:
- `domain`: entities, value objects, domain exceptions and business rules;
- `application`: use cases, DTO, interfaces for repositories, clients, publishers and allocators;
- `infrastructure`: SQLAlchemy repositories, Kafka publishers/consumers, Redis adapters, HTTP clients;
- `interface`: FastAPI routes, schemas, dependencies, exception handlers, WebSocket endpoints.

Dependency direction:

```text
interface -> application -> domain
infrastructure -> application -> domain
```

## Consequences

### Positive

- Domain and application logic are testable without external services.
- Infrastructure implementations can be swapped behind application interfaces.
- New services follow an existing shape instead of inventing local conventions.

### Negative

- Small services carry more files than a simple FastAPI script.
- Mapping between API schemas, DTO, domain entities and ORM models adds boilerplate.
- Strict boundaries require discipline in imports and tests.

### Risks

- Shared abstractions can become too generic if moved into `shared/` too early.
- Interface code can accumulate business decisions if exception handling and validation are not kept clean.

## Alternatives Considered

### Thin FastAPI service with direct SQLAlchemy usage in routes

**Pros**:
- Less boilerplate.
- Faster for simple CRUD endpoints.

**Cons**:
- Harder unit testing.
- Business rules mix with transport and persistence details.
- Refactoring to async workflows or new adapters becomes more expensive.

**Why rejected**: service boundaries and saga flows need explicit use cases and ports.

### Shared framework for all services

**Pros**:
- Less repeated wiring.
- Centralized conventions.

**Cons**:
- Risk of coupling domains through a custom framework.
- Harder to keep service-specific behavior local.

**Why rejected**: shared code should contain contracts and infrastructure helpers, not domain architecture hidden behind a framework.

## Implementation Notes

- `shared/` may contain event contracts, Kafka/Redis/JWT helpers, observability helpers and testing helpers.
- `shared/` must not contain service-specific entities, use cases or repositories.
- New infrastructure dependencies are introduced through application interfaces.

## References

- [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md)
- [docs/ENGINEERING_CONVENTIONS.md](../ENGINEERING_CONVENTIONS.md)
