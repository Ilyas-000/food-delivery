"""Order status enumeration."""

from enum import StrEnum


class OrderStatus(StrEnum):
    """Lifecycle states of an order."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
