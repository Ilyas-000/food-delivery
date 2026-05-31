# Food Delivery Shared

Общий пакет для контрактов и инфраструктурных helpers, которые подключают сервисы Food Delivery Platform.

## Принцип

`shared` содержит общую инфраструктуру и межсервисные контракты. Доменная логика конкретного сервиса остаётся внутри этого сервиса.

В пакет входят:
- Pydantic-контракты Kafka-событий;
- Kafka producer/consumer wrappers;
- Redis client wrapper;
- JWT helpers;
- Prometheus instrumentation helpers;
- request/correlation context helpers;
- базовые исключения;
- pytest summary helper.

В пакет не входят:
- service-specific entities;
- use cases;
- ORM base classes сервисов;
- repositories;
- правила конкретного домена.

## Структура

```text
shared/
├── src/shared/
│   ├── common/
│   │   ├── jwt.py
│   │   ├── kafka.py
│   │   └── redis.py
│   ├── events/
│   ├── exceptions/
│   ├── observability/
│   └── testing/
└── pyproject.toml
```

## События

Event envelope:

```python
from shared.events.base import BaseEvent
```

Доменные события разделены по модулям:

```python
from shared.events.order_events import OrderCreatedEvent, OrderConfirmedEvent
from shared.events.delivery_events import DeliveryAssignedEvent
from shared.events.notification_events import NotificationEmailSentEvent
```

`event_type` должен совпадать с Kafka topic.

## Kafka

```python
from shared.common.kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9093",
    client_id="order-service",
)
await producer.start()
await producer.send("order-service.order.created", event, key=event.aggregate_id)
await producer.stop()
```

## Redis

```python
from shared.common.redis import RedisClient

redis = RedisClient(host="localhost", port=6379, db=1)
await redis.connect()
await redis.set("key", "value", expire=60)
value = await redis.get("key")
await redis.close()
```

## JWT

```python
from shared.common.jwt import create_access_token, decode_token

token = create_access_token(user_id="user-id", role="customer")
payload = decode_token(token, secret_key="secret")
```

## Observability

```python
from shared.observability.prometheus import ServiceMetrics, install_prometheus

metrics = ServiceMetrics("order-service")
install_prometheus(app, metrics, metrics_path="/metrics")
```

## Разработка

```bash
cd shared
uv sync --all-extras
pytest
mypy src/
```
