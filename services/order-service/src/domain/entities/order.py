"""Order aggregate root."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.exceptions.order import InvalidOrderDataError, InvalidOrderTransitionError
from src.domain.value_objects.order_item import OrderItem
from src.domain.value_objects.order_status import OrderStatus


def _utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


@dataclass
class Order:
    """Order aggregate with lifecycle transitions."""

    id: UUID
    user_id: UUID
    restaurant_id: UUID
    items: tuple[OrderItem, ...]
    total_amount: Decimal
    status: OrderStatus = OrderStatus.PENDING
    cancellation_reason: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        user_id: UUID,
        restaurant_id: UUID,
        items: list[OrderItem],
    ) -> "Order":
        """Create a new pending order."""
        if not items:
            raise InvalidOrderDataError("order must contain at least one item")

        total_amount = sum((item.total_amount for item in items), start=Decimal("0.00"))
        if total_amount <= Decimal("0"):
            raise InvalidOrderDataError("order total must be greater than zero")

        now = _utc_now()
        return cls(
            id=uuid4(),
            user_id=user_id,
            restaurant_id=restaurant_id,
            items=tuple(items),
            total_amount=total_amount.quantize(Decimal("0.01")),
            status=OrderStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    def confirm(self) -> None:
        """Move order to confirmed state."""
        self._transition(OrderStatus.CONFIRMED, allowed_from={OrderStatus.PENDING})

    def start_preparing(self) -> None:
        """Move order to preparing state."""
        self._transition(OrderStatus.PREPARING, allowed_from={OrderStatus.CONFIRMED})

    def mark_ready(self) -> None:
        """Move order to ready state."""
        self._transition(OrderStatus.READY, allowed_from={OrderStatus.PREPARING})

    def start_delivery(self) -> None:
        """Move order to delivering state."""
        self._transition(OrderStatus.DELIVERING, allowed_from={OrderStatus.READY})

    def mark_delivered(self) -> None:
        """Move order to delivered state."""
        self._transition(OrderStatus.DELIVERED, allowed_from={OrderStatus.DELIVERING})

    def cancel(self, reason: str) -> None:
        """Cancel order with reason."""
        if not reason.strip():
            raise InvalidOrderDataError("cancellation reason is required")
        self._transition(
            OrderStatus.CANCELLED,
            allowed_from={
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.PREPARING,
                OrderStatus.READY,
                OrderStatus.DELIVERING,
            },
        )
        self.cancellation_reason = reason.strip()

    def _transition(self, new_status: OrderStatus, allowed_from: set[OrderStatus]) -> None:
        """Apply validated status transition."""
        if self.status not in allowed_from:
            raise InvalidOrderTransitionError(
                f"cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = _utc_now()
