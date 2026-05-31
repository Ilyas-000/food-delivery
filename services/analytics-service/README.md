# Analytics Service

Read-only сервис аналитики. Потребляет Kafka-события, нормализует их в аналитические записи и отдаёт отчётные endpoints.

## Назначение

- Потребление операционных событий из Kafka.
- Запись событий в ClickHouse.
- In-memory storage backend для лёгких тестовых сценариев.
- Отдача overview metrics и последних событий.

## API

### Health

- `GET /health`
- `GET /metrics`

### Analytics

- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/events`

## События Kafka

Потребляет:
- `order-service.order.created`
- `order-service.order.confirmed`
- `delivery-service.delivery.assigned`
- `notification-service.notification.email_sent`
- `notification-service.notification.push_sent`

## Хранилище

Backend выбирается настройкой:
- `clickhouse` — запись в ClickHouse table;
- `memory` — in-memory repository.

## Запуск

```bash
make up
curl http://localhost:8007/health
```

Локальный запуск только сервиса:

```bash
make dev-analytics
```

## Конфигурация

Настройки читаются из `services/analytics-service/src/config.py` с префиксом `ANALYTICS_SERVICE_`. Kafka использует `KAFKA_`, ClickHouse — `CLICKHOUSE_`.

Ключевые группы:
- Kafka enabled flag;
- consumer group;
- storage backend;
- ClickHouse table and timeout;
- metrics path.

## Тестирование

```bash
make test-analytics
make test-analytics-unit
```

## Ограничения

- Сервис не выполняет бизнес-операции; он строит read model из событий.
- Consumer readiness нужно отделить от liveness для более точной диагностики.
