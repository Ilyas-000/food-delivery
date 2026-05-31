# Delivery Service

Сервис доставки. Назначает курьера для заказа, хранит текущее assignment-состояние и отдаёт WebSocket tracking.

## Назначение

- Назначение курьера в рамках order saga.
- Отмена назначения как saga-компенсация.
- Обновление координат доставки.
- Завершение доставки.
- WebSocket-трансляция `location_update` и `delivery_completed`.

## API

### Health

- `GET /health`
- `GET /metrics`

### Saga contract

- `POST /api/v1/deliveries/assignments`
- `DELETE /api/v1/deliveries/assignments/{assignment_id}`
- `GET /api/v1/deliveries/orders/{order_id}`

### Delivery tracking

- `POST /api/v1/deliveries/location`
- `POST /api/v1/deliveries/{order_id}/complete`
- `GET /ws/orders/{order_id}` (WebSocket)

## События Kafka

Публикует:
- `delivery-service.delivery.assigned`
- `delivery-service.delivery.location_updated`
- `delivery-service.delivery.completed`

Topic bootstrap также содержит delivery lifecycle topics для дальнейшего расширения.

## Real-time backend

`OrderTrackingBroadcaster` поддерживает два режима:
- `memory` — fanout только внутри процесса;
- `redis` — Redis Pub/Sub fanout между процессами.

Redis Pub/Sub используется для краткоживущих WebSocket updates, а не как durable event log.

## Запуск

```bash
make up
curl http://localhost:8005/health
```

Локальный запуск только сервиса:

```bash
make dev-delivery
```

## Конфигурация

Настройки читаются из `services/delivery-service/src/config.py` с префиксом `DELIVERY_SERVICE_`.

Ключевые группы:
- realtime backend;
- Redis host/port/db/channel prefix;
- Kafka enabled flag;
- mock courier id pool.

## Тестирование

```bash
make test-delivery
make test-delivery-unit
make test-delivery-integration
```

## Ограничения

- Assignment repository in-memory.
- Courier identity берётся из mock-пула, отдельного courier domain пока нет.
- Redis Pub/Sub не сохраняет пропущенные tracking updates для отключённых клиентов.
