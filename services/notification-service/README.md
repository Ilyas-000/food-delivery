# Notification Service

Сервис уведомлений. Потребляет события заказа и доставки из Kafka, создаёт email/push уведомления и публикует события отправки.

## Назначение

- Потребление доменных событий из Kafka.
- Отправка email-уведомлений через mock client.
- Отправка push-уведомлений через mock client.
- Чтение истории уведомлений.
- Публикация событий отправки уведомлений.

## API

### Health

- `GET /health`
- `GET /metrics`

### Notifications

- `POST /api/v1/notifications/email`
- `POST /api/v1/notifications/push`
- `GET /api/v1/notifications`
- `GET /api/v1/notifications/{notification_id}`

## События Kafka

Потребляет:
- `order-service.order.created`
- `order-service.order.confirmed`
- `delivery-service.delivery.assigned`

Публикует:
- `notification-service.notification.email_sent`
- `notification-service.notification.push_sent`

## Запуск

```bash
make up
curl http://localhost:8006/health
```

Локальный запуск только сервиса:

```bash
make dev-notification
```

## Конфигурация

Настройки читаются из `services/notification-service/src/config.py` с префиксом `NOTIFICATION_SERVICE_`. Общие настройки Kafka читаются через `KAFKA_`.

Ключевые группы:
- Kafka enabled flag;
- consumer group;
- mock email domain;
- mock push prefix;
- metrics path.

## Тестирование

```bash
make test-notification
make test-notification-unit
```

## Ограничения

- Email и push clients являются mock-адаптерами.
- История уведомлений хранится in-memory.
- Consumer readiness нужно отделить от liveness для более точной диагностики.
