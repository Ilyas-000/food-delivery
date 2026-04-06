"""Contracts for order domain event publishing."""

from abc import ABC, abstractmethod

from src.domain.entities.order import Order


class IOrderEventPublisher(ABC):
    """Order event publisher contract."""

    @abstractmethod
    async def publish_order_created(self, order: Order) -> None:
        """Publish order created event."""

    @abstractmethod
    async def publish_order_confirmed(self, order: Order) -> None:
        """Publish order confirmed event."""
