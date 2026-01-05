# Food Delivery Shared

Shared code and utilities for all Food Delivery microservices.

## Structure

```
shared/
├── src/shared/
│   ├── events/         # Event models (Pydantic schemas)
│   ├── common/         # Common utilities
│   │   ├── kafka.py    # Kafka producer/consumer wrappers
│   │   ├── redis.py    # Redis client wrapper
│   │   ├── postgres.py # SQLAlchemy base utilities
│   │   └── auth.py     # JWT utilities
│   └── exceptions/     # Base exceptions
└── tests/              # Unit tests
```

## Installation

This package is automatically installed in the uv workspace. Services can use it directly:

```python
from shared.events import OrderCreatedEvent
from shared.common.kafka import KafkaProducer
from shared.exceptions import DomainException
```

## Usage

### Events

```python
from shared.events import BaseEvent

class OrderCreatedEvent(BaseEvent):
    order_id: str
    user_id: str
    total_amount: Decimal
```

### Kafka

```python
from shared.common.kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers="localhost:9092")
await producer.send("order.created", event.model_dump_json())
```

### Redis

```python
from shared.common.redis import RedisClient

redis = RedisClient(host="localhost", port=6379)
await redis.set("key", "value", expire=3600)
```

## Development

```bash
# Install dependencies
cd shared
uv sync --all-extras

# Run tests
pytest

# Type checking
mypy src/
```
