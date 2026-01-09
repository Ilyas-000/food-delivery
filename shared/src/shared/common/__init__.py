"""
Shared common utilities for all services.

What's in shared/common:
- JWT utilities (all services use same JWT format)
- Kafka clients (consistent event publishing/consuming)
- Redis client (consistent caching/pubsub)

What's NOT in shared/common:
- ORM base classes (each service has its own DB setup)
- Password hashing (each service chooses bcrypt/argon2/passlib)
- Domain logic (belongs to individual services)

Philosophy: Share infrastructure, not domain logic.
"""
