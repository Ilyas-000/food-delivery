# Notification Service

Event-driven service for customer notifications in the Food Delivery platform.

## Scope

- Consume domain events from Kafka
- Send mock email notifications
- Send mock push notifications
- Store sent notifications in memory for the current phase

## API Endpoints

- `GET /health`
- `POST /api/v1/notifications/email`
- `POST /api/v1/notifications/push`
- `GET /api/v1/notifications`
- `GET /api/v1/notifications/{notification_id}`

## Consumed Events

- `order-service.order.created`
- `order-service.order.confirmed`
- `delivery-service.delivery.assigned`

## Produced Events

- `notification-service.notification.email_sent`
- `notification-service.notification.push_sent`

## Notes

- Email and push delivery are mock implementations in this phase.
- Kafka consumption/publishing is optional and controlled by `NOTIFICATION_SERVICE_KAFKA_ENABLED`.
- Recipient addressing is mock-stage: user ids are converted into deterministic email/push targets.
