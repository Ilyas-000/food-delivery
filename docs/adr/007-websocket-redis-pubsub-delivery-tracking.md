# ADR-007: WebSocket and Redis Pub/Sub for Delivery Tracking

**Status**: Accepted
**Date**: 2026-05-31
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

Delivery tracking needs low-latency updates for a specific order. Clients connect through API Gateway, while Delivery Service owns delivery state and tracking events.

The mechanism must support multiple gateway/service instances in the future without storing every location update as a durable domain event.

## Decision

Delivery tracking uses:
- public WebSocket endpoint `GET /ws/orders/{order_id}` through API Gateway;
- Delivery Service WebSocket endpoint with the same path;
- `OrderTrackingBroadcaster` in Delivery Service;
- Redis Pub/Sub for cross-process fanout when `DELIVERY_SERVICE_REALTIME_BACKEND=redis`;
- in-memory fanout as a local/test fallback.

Kafka remains the transport for durable domain events. Redis Pub/Sub is used only for ephemeral real-time fanout.

## Consequences

### Positive

- Clients receive location and completion updates without polling.
- Redis allows multiple process instances to broadcast to subscribed WebSocket clients.
- The design keeps high-frequency location updates separate from durable Kafka event streams.

### Negative

- Redis Pub/Sub does not retain messages for disconnected clients.
- In-memory fallback works only inside one process.
- WebSocket lifecycle adds connection management and cleanup concerns.

### Risks

- Missed location updates are possible during reconnects.
- A high number of subscribers per order can create fanout pressure.
- Redis outage falls back to local broadcast only for clients connected to the publishing process.

## Alternatives Considered

### HTTP polling

**Pros**:
- Simple client and server model.
- No long-lived connections.

**Cons**:
- Higher latency or higher request volume.
- Poor fit for courier location updates.

**Why rejected**: tracking is a real-time workflow.

### Kafka directly to WebSocket broadcaster

**Pros**:
- Durable stream can be replayed.
- One event bus for all asynchronous communication.

**Cons**:
- Higher latency and operational overhead for ephemeral UI updates.
- Location updates can create unnecessary Kafka volume.

**Why rejected**: delivery tracking fanout is short-lived and per-order; Redis Pub/Sub fits this better.

## Implementation Notes

- Gateway proxy: `services/api-gateway/src/routes/proxy.py`
- WebSocket endpoint: `services/delivery-service/src/interface/api/ws/order_tracking.py`
- Broadcaster: `services/delivery-service/src/interface/realtime/order_tracking_broadcaster.py`
- Delivery routes publish `location_update` and `delivery_completed` payloads through the broadcaster.

## References

- [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md)
