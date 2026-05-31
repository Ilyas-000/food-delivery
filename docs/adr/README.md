# Architecture Decision Records (ADRs)

This directory stores Architecture Decision Records for the Food Delivery project.

## ADR Lifecycle

1. **Proposed** - Draft under discussion
2. **Accepted** - Decision approved
3. **Deprecated** - No longer recommended
4. **Superseded** - Replaced by a newer ADR

## Existing ADR Files (in this directory)

| # | File | Title | Status | Date |
|---|---|---|---|---|
| 003 | `003-restaurant-service-architecture.md` | Restaurant Service Architecture | Proposed | 2026-01-31 |
| 004 | `004-observability-stack.md` | Monitoring and Observability Stack | Accepted | 2026-04-07 |

## Planned ADR Topics (not created yet)

- Microservices architecture baseline
- Saga orchestration strategy
- Kafka vs RabbitMQ for event bus
- Outbox pattern for reliable events
- Clean Architecture conventions across services
- WebSocket + Redis Pub/Sub for delivery tracking
- PostgreSQL database-per-service strategy
- Async Python operational guidelines

## How to Create a New ADR

1. Copy template:
   ```bash
   cp docs/adr/template.md docs/adr/XXX-short-title.md
   ```
2. Use sequential numeric prefix (`001`, `002`, ...).
3. Fill Context, Decision, Consequences, Alternatives.
4. Mark status in the document (`Proposed` -> `Accepted` when approved).

## Template

Use [template.md](template.md).
