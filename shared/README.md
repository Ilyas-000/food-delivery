# Food Delivery Shared

Shared code and utilities for all Food Delivery microservices.

## Structure

```
shared/
├── src/shared/
│   ├── events/         # Event models (Pydantic schemas for service contracts)
│   ├── common/         # Common infrastructure utilities
│   │   ├── kafka.py    # Kafka producer/consumer wrappers
│   │   ├── redis.py    # Redis client wrapper
│   │   └── jwt.py      # JWT token utilities
│   ├── observability/  # Shared Prometheus instrumentation helpers
│   └── exceptions/     # Base exceptions
└── tests/              # Unit tests
```

## Philosophy

**Share infrastructure, not domain logic.**

This library contains:
- Infrastructure clients (Kafka, Redis)
- Event contracts (cross-service communication)
- JWT utilities (authentication)
- Observability helpers (Prometheus HTTP instrumentation)
- Request context helpers (request/correlation ids + request-level logging)

This library does NOT contain:
- ORM base classes (each service manages own DB)
- Password hashing (domain-specific to User Service)
- Domain entities or business logic

## Installation

This package is automatically installed in the uv workspace. Services can use it directly:

```python
from shared.events.order_events import OrderCreatedEvent
from shared.common.kafka import KafkaProducer
from shared.common.redis import RedisClient
from shared.common.jwt import create_access_token
```

## Usage

### Events

Event definitions are in separate modules by domain:

```python
# Events are defined in shared/events/ directory
# Services import explicitly:
from shared.events.order_events import OrderCreatedEvent, OrderConfirmedEvent
from shared.events.payment_events import PaymentReservedEvent

# Each service defines its own events in shared/events/{service}_events.py
```

### Kafka

```python
from shared.common.kafka import KafkaConsumer, KafkaProducer

# Producer
producer = KafkaProducer(bootstrap_servers="localhost:9092")
await producer.send("order-service.order.created", event.model_dump_json())

# Consumer
consumer = KafkaConsumer(
    topic="order-service.order.created",
    bootstrap_servers="localhost:9092",
    group_id="user-service-group"
)
async for message in consumer:
    # Process message
    pass
```

### Redis

```python
from shared.common.redis import RedisClient

redis = RedisClient(host="localhost", port=6379)
await redis.set("key", "value", expire=3600)
value = await redis.get("key")
```

### JWT Utilities

```python
from shared.common.jwt import create_access_token, decode_token

# Create token
token = create_access_token(user_id="123", role="customer")

# Decode and verify
payload = decode_token(token, secret_key="...")
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
