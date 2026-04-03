from __future__ import annotations

from typing import Literal

from shared.events.base import BaseEvent


class DeliveryAssignedEvent(BaseEvent):
    """Delivery assignment event."""

    event_type: Literal["delivery-service.delivery.assigned"] = "delivery-service.delivery.assigned"
    aggregate_type: Literal["delivery"] = "delivery"

    order_id: str


class DeliveryCompletedEvent(BaseEvent):
    """Delivery completed event."""

    event_type: Literal[
        "delivery-service.delivery.completed"
    ] = "delivery-service.delivery.completed"
    aggregate_type: Literal["delivery"] = "delivery"

    order_id: str


class DeliveryLocationUpdatedEvent(BaseEvent):
    """Delivery location update event."""

    event_type: Literal[
        "delivery-service.delivery.location_updated"
    ] = "delivery-service.delivery.location_updated"
    aggregate_type: Literal["delivery"] = "delivery"

    order_id: str
    latitude: float
    longitude: float
