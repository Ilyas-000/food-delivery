"""Application contracts for external service clients used by saga steps."""

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from src.domain.value_objects.order_item import OrderItem


class IRestaurantServiceClient(ABC):
    """Contract for restaurant service interactions."""

    @abstractmethod
    async def validate_items(self, restaurant_id: UUID, items: tuple[OrderItem, ...]) -> None:
        """Validate that all menu items can be ordered for a restaurant."""


class IPaymentServiceClient(ABC):
    """Contract for payment reservation interactions."""

    @abstractmethod
    async def reserve(self, order_id: UUID, user_id: UUID, amount: Decimal, currency: str) -> str:
        """Reserve payment funds and return reservation id."""

    @abstractmethod
    async def release(self, reservation_id: str) -> None:
        """Release a previously created payment reservation."""


class IDeliveryServiceClient(ABC):
    """Contract for courier assignment interactions."""

    @abstractmethod
    async def assign(self, order_id: UUID, restaurant_id: UUID) -> str:
        """Assign courier for order and return assignment id."""

    @abstractmethod
    async def cancel(self, assignment_id: str) -> None:
        """Cancel previously created courier assignment."""
