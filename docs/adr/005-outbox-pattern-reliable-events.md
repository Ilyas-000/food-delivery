# ADR-005: Outbox Pattern for Reliable Events

**Status**: Proposed
**Date**: 2026-05-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

Several services publish Kafka events after changing local state. The current publishers are best-effort: if the database write succeeds and Kafka publish fails, the state change remains committed while the event can be lost.

This affects order, restaurant and review flows most directly because those services have PostgreSQL-backed state and publish domain events.

## Decision

Adopt transactional outbox for services that persist state and publish Kafka events.

The service transaction writes:
- the business row;
- an `outbox_events` row with event type, aggregate id, payload, schema version, status and timestamps.

A dispatcher publishes pending outbox rows to Kafka and marks them as published after successful send. Failed sends remain retryable. Consumers remain idempotent because Kafka and the dispatcher can deliver duplicates.

## Consequences

### Positive

- State changes and event creation become atomic within one service database transaction.
- Kafka outages no longer cause silent loss of already committed domain changes.
- Retry behavior is explicit and observable.

### Negative

- Each PostgreSQL-backed event publisher needs an outbox table and dispatcher.
- Events can be delayed until the dispatcher publishes them.
- Consumers must continue handling duplicates.

### Risks

- A stuck dispatcher can grow the outbox table.
- Bad payload versioning can make old rows unpublishable after schema changes.
- Publishing order needs clear rules when several events exist for the same aggregate.

## Alternatives Considered

### Keep best-effort publishing

**Pros**:
- Minimal code and no extra database table.
- Simple for local development.

**Cons**:
- Event loss is possible after successful state changes.
- Recovery requires manual reconstruction from service state.

**Why rejected**: the risk is too high for order and review flows once events drive downstream behavior.

### Kafka transaction without database outbox

**Pros**:
- Kafka publish can be transactional inside Kafka.

**Cons**:
- Does not make PostgreSQL commit and Kafka publish one atomic operation.
- Still leaves a dual-write problem.

**Why rejected**: the primary consistency boundary is the service database transaction.

## Implementation Notes

- Start with Order Service because order events feed notification and analytics.
- Reuse the event envelope from `shared/src/shared/events/base.py`.
- Add per-service migrations for `outbox_events`.
- Dispatcher can run in-process initially, then move to a worker if needed.
- Add metrics for pending rows, publish failures and oldest pending age.

## References

- [002-saga-orchestration-strategy.md](002-saga-orchestration-strategy.md)
- [006-clean-architecture-conventions.md](006-clean-architecture-conventions.md)
