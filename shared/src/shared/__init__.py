"""
Shared library for food-delivery microservices.

What's shared:
- events/ - Event definitions (contracts between services)
- common/ - Infrastructure clients (Kafka, Redis, JWT)

What's NOT shared:
- Domain logic (each service has its own)
- ORM models (each service manages its own database)
- Use cases (business logic specific to each service)

Philosophy: Share contracts and infrastructure, not domain.

Import explicitly:
    from shared.events.order_events import OrderCreated
    from shared.common.kafka import KafkaProducer
    from shared.common.jwt import create_access_token
"""
