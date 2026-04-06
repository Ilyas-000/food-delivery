"""Unit tests for notification application layer."""

import pytest

from shared.events.delivery_events import DeliveryAssignedEvent
from shared.events.order_events import OrderConfirmedEvent, OrderCreatedEvent
from src.application.dto.notification import SendEmailDTO
from src.interface.dependencies.notification import (
    get_email_client,
    get_notification_event_processor,
    get_notification_repository,
    get_send_email_use_case,
)

EXPECTED_EMAIL_MESSAGES = 3


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_send_email_use_case_persists_notification() -> None:
    use_case = await get_send_email_use_case()

    result = await use_case.execute(
        SendEmailDTO(
            recipient="user-1@notifications.local",
            template_name="order_created_email",
            template_context={"order_id": "order-1"},
            aggregate_id="order-1",
            event_type="order-service.order.created",
            user_id="user-1",
        )
    )

    repository = await get_notification_repository()
    stored = await repository.get_by_id(result.id)

    assert stored is not None
    assert stored.provider_message_id == "email-1"
    assert stored.recipient == "user-1@notifications.local"


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_event_processor_sends_created_confirmed_and_assignment_notifications() -> None:
    processor = get_notification_event_processor()
    email_client = await get_email_client()

    created_event = OrderCreatedEvent(
        aggregate_id="order-1",
        user_id="user-1",
        restaurant_id="restaurant-1",
        total_amount="450.00",
    )
    confirmed_event = OrderConfirmedEvent(
        aggregate_id="order-1",
        user_id="user-1",
    )
    assigned_event = DeliveryAssignedEvent(
        aggregate_id="assignment-1",
        order_id="order-1",
        restaurant_id="restaurant-1",
    )

    await processor.process_event(created_event.model_dump(mode="json"))
    await processor.process_event(confirmed_event.model_dump(mode="json"))
    await processor.process_event(assigned_event.model_dump(mode="json"))

    assert len(email_client.messages) == EXPECTED_EMAIL_MESSAGES
    assert email_client.messages[0].subject == "Order order-1 received"
    assert email_client.messages[1].subject == "Order order-1 confirmed"
    assert email_client.messages[2].subject == "Courier assigned for order order-1"
