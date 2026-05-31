# ADR-002: Saga Orchestration Strategy

**Status**: Accepted
**Date**: 2026-05-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

Creating an order touches multiple services:
- Restaurant Service validates restaurant and menu items.
- Payment Service reserves funds.
- Delivery Service assigns a courier.

A single database transaction cannot span these services. The system needs a way to coordinate the flow and compensate completed side effects when a later step fails.

## Decision

Order Service is the saga orchestrator for order creation.

The current step order is:

1. Persist a new order.
2. Publish `order-service.order.created` best-effort.
3. Validate menu items through Restaurant Service.
4. Reserve payment through Payment Service.
5. Assign courier through Delivery Service.
6. Confirm the order.
7. Publish `order-service.order.confirmed` best-effort.

If a step fails, Order Service runs compensations for completed steps in reverse order:
- release payment reservation;
- cancel delivery assignment.

Validation has no remote side effect and its compensation is a no-op.

## Consequences

### Positive

- One service owns the order state machine and orchestration logic.
- Compensation behavior is explicit and covered by use-case tests.
- Downstream service contracts stay narrow: reserve/release, assign/cancel, validate.

### Negative

- `POST /api/v1/orders` is synchronous and waits for all remote steps.
- Saga step state is not persisted separately from the order.
- Recovery after process failure between steps needs additional work.

### Risks

- Remote call latency directly affects client latency.
- Partial failure recovery depends on downstream idempotency and compensation correctness.
- Event publication is not atomic with order persistence until outbox is implemented.

## Alternatives Considered

### Choreography through Kafka only

**Pros**:
- Less direct coupling between services.
- Natural async processing.

**Cons**:
- Harder to understand and debug the order state machine.
- More complex client-facing status semantics.
- Requires stronger idempotency and recovery discipline from the beginning.

**Why rejected**: order creation currently benefits from one explicit coordinator and direct compensation logic.

### Distributed transaction / 2PC

**Pros**:
- Stronger atomicity across resources in theory.

**Cons**:
- Poor fit for independent HTTP services.
- Operationally complex and brittle under partial failures.

**Why rejected**: service autonomy and explicit compensation are preferred over distributed locking.

## Implementation Notes

- Use case: `services/order-service/src/application/use_cases/create_order.py`
- Saga ports: `services/order-service/src/application/interfaces/saga_step.py`
- HTTP steps: `services/order-service/src/infrastructure/saga/http_steps.py`
- HTTP clients: `services/order-service/src/infrastructure/clients/http_service_clients.py`
- Order repository: `services/order-service/src/infrastructure/database/repositories/sqlalchemy_order_repository.py`

## References

- [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md)
- [005-outbox-pattern-reliable-events.md](005-outbox-pattern-reliable-events.md)
