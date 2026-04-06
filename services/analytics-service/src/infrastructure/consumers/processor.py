"""Analytics event processor."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from shared.events.delivery_events import DeliveryAssignedEvent
from shared.events.notification_events import (
    NotificationEmailSentEvent,
    NotificationPushSentEvent,
)
from shared.events.order_events import OrderConfirmedEvent, OrderCreatedEvent
from src.application.dto.analytics import IngestAnalyticsEventDTO
from src.application.use_cases.ingest_event import IngestAnalyticsEventUseCase

logger = structlog.get_logger(__name__)


class AnalyticsEventProcessor:
    """Map supported domain events into analytics records."""

    def __init__(self, *, ingest_event_use_case: IngestAnalyticsEventUseCase) -> None:
        self._ingest_event_use_case = ingest_event_use_case

    async def process_event(self, payload: dict[str, Any]) -> None:
        """Decode supported event payload and store analytics record."""
        event_type = str(payload.get("event_type", "")).strip()
        dto: IngestAnalyticsEventDTO | None
        if event_type == OrderCreatedEvent.model_fields["event_type"].default:
            dto = self._build_order_created_dto(OrderCreatedEvent.model_validate(payload), payload)
        elif event_type == OrderConfirmedEvent.model_fields["event_type"].default:
            dto = self._build_order_confirmed_dto(
                OrderConfirmedEvent.model_validate(payload),
                payload,
            )
        elif event_type == DeliveryAssignedEvent.model_fields["event_type"].default:
            dto = self._build_delivery_assigned_dto(
                DeliveryAssignedEvent.model_validate(payload),
                payload,
            )
        elif event_type == NotificationEmailSentEvent.model_fields["event_type"].default:
            dto = self._build_email_sent_dto(
                NotificationEmailSentEvent.model_validate(payload),
                payload,
            )
        elif event_type == NotificationPushSentEvent.model_fields["event_type"].default:
            dto = self._build_push_sent_dto(
                NotificationPushSentEvent.model_validate(payload),
                payload,
            )
        else:
            dto = self._build_generic_dto(payload)

        if dto is None:
            logger.debug("analytics.processor.unsupported_event", event_type=event_type)
            return

        await self._ingest_event_use_case.execute(dto)

    def _build_order_created_dto(
        self,
        event: OrderCreatedEvent,
        payload: dict[str, Any],
    ) -> IngestAnalyticsEventDTO:
        return IngestAnalyticsEventDTO(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            order_id=event.aggregate_id,
            restaurant_id=event.restaurant_id,
            amount=event.total_amount,
            currency=event.currency,
            payload=payload,
        )

    def _build_order_confirmed_dto(
        self,
        event: OrderConfirmedEvent,
        payload: dict[str, Any],
    ) -> IngestAnalyticsEventDTO:
        return IngestAnalyticsEventDTO(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            order_id=event.aggregate_id,
            payload=payload,
        )

    def _build_delivery_assigned_dto(
        self,
        event: DeliveryAssignedEvent,
        payload: dict[str, Any],
    ) -> IngestAnalyticsEventDTO:
        return IngestAnalyticsEventDTO(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            order_id=event.order_id,
            restaurant_id=event.restaurant_id,
            payload=payload,
        )

    def _build_email_sent_dto(
        self,
        event: NotificationEmailSentEvent,
        payload: dict[str, Any],
    ) -> IngestAnalyticsEventDTO:
        return IngestAnalyticsEventDTO(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            notification_type=event.notification_type,
            recipient=event.recipient,
            template_name=event.template_name,
            source_event_type=event.source_event_type,
            payload=payload,
        )

    def _build_push_sent_dto(
        self,
        event: NotificationPushSentEvent,
        payload: dict[str, Any],
    ) -> IngestAnalyticsEventDTO:
        return IngestAnalyticsEventDTO(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            notification_type=event.notification_type,
            recipient=event.recipient,
            template_name=event.template_name,
            source_event_type=event.source_event_type,
            payload=payload,
        )

    def _build_generic_dto(self, payload: dict[str, Any]) -> IngestAnalyticsEventDTO | None:
        event_id = payload.get("event_id")
        event_type = payload.get("event_type")
        aggregate_id = payload.get("aggregate_id")
        aggregate_type = payload.get("aggregate_type")
        occurred_at = payload.get("occurred_at")
        if not all([event_id, event_type, aggregate_id, aggregate_type, occurred_at]):
            return None

        return IngestAnalyticsEventDTO(
            event_id=UUID(str(event_id)),
            event_type=str(event_type),
            aggregate_id=str(aggregate_id),
            aggregate_type=str(aggregate_type),
            occurred_at=datetime.fromisoformat(str(occurred_at)),
            user_id=str(payload["user_id"]) if payload.get("user_id") is not None else None,
            payload=payload,
        )
