"""Notification event processor."""

from typing import Any

import structlog

from shared.events.delivery_events import DeliveryAssignedEvent
from shared.events.order_events import OrderConfirmedEvent, OrderCreatedEvent
from src.application.dto.notification import SendEmailDTO, SendPushDTO
from src.application.use_cases.send_email import SendEmailUseCase
from src.application.use_cases.send_push import SendPushUseCase

logger = structlog.get_logger(__name__)


class NotificationEventProcessor:
    """Map domain events to notification delivery use cases."""

    def __init__(
        self,
        *,
        send_email_use_case: SendEmailUseCase,
        send_push_use_case: SendPushUseCase,
        email_domain: str,
        push_prefix: str,
    ) -> None:
        self._send_email_use_case = send_email_use_case
        self._send_push_use_case = send_push_use_case
        self._email_domain = email_domain
        self._push_prefix = push_prefix
        self._order_recipients: dict[str, str] = {}

    async def process_event(self, payload: dict[str, Any]) -> None:
        """Process a decoded event payload."""
        event_type = str(payload.get("event_type", "")).strip()
        if event_type == OrderCreatedEvent.model_fields["event_type"].default:
            await self._handle_order_created(OrderCreatedEvent.model_validate(payload))
            return
        if event_type == OrderConfirmedEvent.model_fields["event_type"].default:
            await self._handle_order_confirmed(OrderConfirmedEvent.model_validate(payload))
            return
        if event_type == DeliveryAssignedEvent.model_fields["event_type"].default:
            await self._handle_delivery_assigned(DeliveryAssignedEvent.model_validate(payload))
            return

        logger.debug("notification.processor.unsupported_event", event_type=event_type)

    def clear(self) -> None:
        """Reset remembered order recipient mapping."""
        self._order_recipients.clear()

    async def _handle_order_created(self, event: OrderCreatedEvent) -> None:
        self._order_recipients[event.aggregate_id] = event.user_id
        await self._send_email_use_case.execute(
            SendEmailDTO(
                recipient=self._build_email_recipient(event.user_id),
                template_name="order_created_email",
                template_context={"order_id": event.aggregate_id},
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                user_id=event.user_id,
            )
        )

    async def _handle_order_confirmed(self, event: OrderConfirmedEvent) -> None:
        self._order_recipients[event.aggregate_id] = event.user_id
        await self._send_email_use_case.execute(
            SendEmailDTO(
                recipient=self._build_email_recipient(event.user_id),
                template_name="order_confirmed_email",
                template_context={"order_id": event.aggregate_id},
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                user_id=event.user_id,
            )
        )
        await self._send_push_use_case.execute(
            SendPushDTO(
                recipient=self._build_push_recipient(event.user_id),
                template_name="order_confirmed_push",
                template_context={"order_id": event.aggregate_id},
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                user_id=event.user_id,
            )
        )

    async def _handle_delivery_assigned(self, event: DeliveryAssignedEvent) -> None:
        user_id = self._order_recipients.get(event.order_id)
        if user_id is None:
            logger.warning(
                "notification.processor.delivery_assigned_missing_user",
                order_id=event.order_id,
                assignment_id=event.aggregate_id,
            )
            return

        await self._send_email_use_case.execute(
            SendEmailDTO(
                recipient=self._build_email_recipient(user_id),
                template_name="courier_assigned_email",
                template_context={"order_id": event.order_id},
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                user_id=user_id,
            )
        )
        await self._send_push_use_case.execute(
            SendPushDTO(
                recipient=self._build_push_recipient(user_id),
                template_name="courier_assigned_push",
                template_context={"order_id": event.order_id},
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                user_id=user_id,
            )
        )

    def _build_email_recipient(self, user_id: str) -> str:
        safe_user_id = user_id.strip().replace("@", "_")
        return f"{safe_user_id}@{self._email_domain}"

    def _build_push_recipient(self, user_id: str) -> str:
        return f"{self._push_prefix}:{user_id.strip()}"
