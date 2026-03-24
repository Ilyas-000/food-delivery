# Order Service

Order creation and saga orchestration service.

## Endpoints

- `GET /health`
- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`

## Notes

- Repository backend is configurable via `ORDER_SERVICE_REPOSITORY_BACKEND`:
  - `memory` (default) for lightweight local/test mode
  - `postgres` for SQLAlchemy + Alembic mode
- Saga flow backend is configurable via `ORDER_SERVICE_SAGA_BACKEND`:
  - `mock` (default) for local/test mode
  - `http` to call Restaurant/Payment/Delivery service APIs
- HTTP mode expects service contracts:
  - `POST/DELETE /api/v1/payments/reservations`
  - `POST/DELETE /api/v1/deliveries/assignments`
