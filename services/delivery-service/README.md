# Delivery Service

Courier assignment and delivery tracking service for order saga orchestration.

Phase 5 status: completed in contract-stage (REST lifecycle + WebSocket tracking).

## Endpoints

Public (через API Gateway):
- `POST /api/v1/deliveries/location`
- `POST /api/v1/deliveries/{order_id}/complete`
- `GET /ws/orders/{order_id}` (WebSocket)

Internal saga contract (service-to-service):
- `GET /health`
- `POST /api/v1/deliveries/assignments`
- `DELETE /api/v1/deliveries/assignments/{assignment_id}`

## Notes

- Current storage backend is in-memory.
- Real-time backend is configurable via `DELIVERY_SERVICE_REALTIME_BACKEND` (`memory` or `redis`).
- Recommended runtime for Phase 5: `DELIVERY_SERVICE_REALTIME_BACKEND=redis`.
- Contract is used by `order-service` in `ORDER_SERVICE_SAGA_BACKEND=http` mode.
- External client traffic should enter via `api-gateway`; direct calls to `delivery-service` are internal/dev mode.
- WebSocket broadcasts:
  - `location_update`
  - `delivery_completed`
