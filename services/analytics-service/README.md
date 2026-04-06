# Analytics Service

Read-only analytics service for operational reporting in the Food Delivery platform.

Phase status: `Phase 7 completed`.

## Scope

- Consume operational events from Kafka
- Store normalized analytics rows in ClickHouse
- Expose basic reporting endpoints for overview metrics and recent events

## Consumed Events

- `order-service.order.created`
- `order-service.order.confirmed`
- `delivery-service.delivery.assigned`
- `notification-service.notification.email_sent`
- `notification-service.notification.push_sent`

## API Endpoints

- `GET /health`
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/events`

## Notes

- Storage backend is configurable via `ANALYTICS_SERVICE_STORAGE_BACKEND`:
  - `clickhouse` for Phase 7 runtime
  - `memory` for lightweight tests/dev mode
- Kafka consumption is controlled by `ANALYTICS_SERVICE_KAFKA_ENABLED`.
- External access should go through `api-gateway`.
- Docker Compose ships a dev/test ClickHouse user override so service-to-service HTTP access works inside the compose network.
