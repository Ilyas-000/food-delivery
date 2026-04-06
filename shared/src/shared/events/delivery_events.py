from __future__ import annotations

from typing import Literal

from shared.events.base import BaseEvent


class DeliveryAssignedEvent(BaseEvent):
    """Delivery assigned event."""

    event_type: Literal["delivery-service.delivery.assigned"] = "delivery-service.delivery.assigned"
    aggregate_type: Literal["delivery"] = "delivery"

    order_id: str
    restaurant_id: str
