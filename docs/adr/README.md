# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Food Delivery project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

ADRs help us:
- 📝 Document why we made specific architectural choices
- 🤔 Consider trade-offs before making decisions
- 🔄 Onboard new team members faster
- 📚 Build institutional knowledge
- 🎯 Provide shared context for architectural decisions

## When to Create an ADR?

Create an ADR when making decisions about:
- Technology choices (databases, message brokers, frameworks)
- Architectural patterns (Saga, CQRS, Event Sourcing)
- API design and contracts
- Data models and schemas
- Security and authentication approaches
- Deployment and infrastructure
- Performance optimizations with trade-offs

## How to Create an ADR?

1. Copy the template:
   ```bash
   cp docs/adr/template.md docs/adr/XXX-your-decision-title.md
   ```

2. Use sequential numbering (001, 002, 003, etc.)

3. Fill in all sections:
   - **Context**: Why is this decision needed?
   - **Decision**: What did we decide?
   - **Consequences**: What are the impacts?
   - **Alternatives**: What else did we consider?

4. Discuss with team

5. Mark as **Accepted** when finalized

## ADR Lifecycle

1. **Proposed** - Draft, under discussion
2. **Accepted** - Decision made and approved
3. **Deprecated** - No longer recommended but not replaced
4. **Superseded** - Replaced by a newer ADR (link to it)

## Index of ADRs

| # | Title | Status | Date |
|---|-------|--------|------|
| [001](001-microservices-architecture.md) | Microservices Architecture | Proposed | 2026-01-04 |
| [002](002-saga-pattern-orchestration.md) | Saga Pattern (Orchestration) | Proposed | TBD |
| [003](003-restaurant-service-architecture.md) | Restaurant Service Architecture | Proposed | 2026-01-31 |
| [004](004-kafka-vs-rabbitmq.md) | Kafka vs RabbitMQ for Event Bus | Proposed | TBD |
| [005](005-outbox-pattern.md) | Outbox Pattern for Reliable Events | Proposed | TBD |
| [006](006-clean-architecture.md) | Clean Architecture in Services | Proposed | TBD |
| [007](007-websocket-redis-pubsub.md) | WebSocket + Redis Pub/Sub for Tracking | Proposed | TBD |
| [008](008-postgresql-per-service.md) | Separate PostgreSQL DB per Service | Proposed | TBD |
| [009](009-python-async.md) | Python Async/Await for I/O Operations | Proposed | TBD |

## Template

See [template.md](template.md) for the ADR template.

## Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR Tools](https://github.com/npryce/adr-tools)

---

**Note**: ADRs are living documents. They can be updated as we learn more, but significant changes should result in a new ADR that supersedes the old one.
