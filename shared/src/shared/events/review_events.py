from __future__ import annotations

from typing import Literal

from shared.events.base import BaseEvent


class ReviewCreatedEvent(BaseEvent):
    """Review created event."""

    event_type: Literal["review-service.review.created"] = "review-service.review.created"
    aggregate_type: Literal["review"] = "review"

    order_id: str
    target_type: str
    target_id: str
    rating: int
