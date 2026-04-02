# Payment Service

Payment lifecycle service for order saga orchestration.

## Endpoints

- `GET /health`
- `POST /api/v1/payments/reservations`
- `DELETE /api/v1/payments/reservations/{reservation_id}`
- `GET /api/v1/payments/history`
- `GET /api/v1/payments/{payment_id}`
- `POST /api/v1/payments/{payment_id}/confirm`
- `POST /api/v1/payments/{payment_id}/refund`

## Notes

- Current storage backend is in-memory (phase 4 start).
- Reservation/release contract remains compatible for `order-service` HTTP saga mode.
- `Idempotency-Key` header is supported for reservation endpoint.
