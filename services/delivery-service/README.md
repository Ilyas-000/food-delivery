# Delivery Service

Courier assignment contract for order saga orchestration.

## Endpoints

- `GET /health`
- `POST /api/v1/deliveries/assignments`
- `DELETE /api/v1/deliveries/assignments/{assignment_id}`

## Notes

- Current storage backend is in-memory.
- Contract is used by `order-service` in `ORDER_SERVICE_SAGA_BACKEND=http` mode.
