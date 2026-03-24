# Payment Service

Payment reservation contract for order saga orchestration.

## Endpoints

- `GET /health`
- `POST /api/v1/payments/reservations`
- `DELETE /api/v1/payments/reservations/{reservation_id}`

## Notes

- Current storage backend is in-memory.
- Contract is used by `order-service` in `ORDER_SERVICE_SAGA_BACKEND=http` mode.
