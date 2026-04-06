"""Unit tests for notification entity."""

import pytest

from src.domain.entities.notification import Notification
from src.domain.exceptions.notification import NotificationValidationError
from src.domain.value_objects.notification_status import NotificationStatus
from src.domain.value_objects.notification_type import NotificationType


@pytest.mark.unit()
def test_notification_create_requires_non_empty_recipient() -> None:
    with pytest.raises(NotificationValidationError, match="recipient"):
        Notification.create(
            notification_type=NotificationType.EMAIL,
            recipient="  ",
            template_name="order_created_email",
            subject="Order received",
            body="Body",
            aggregate_id="order-1",
            event_type="order-service.order.created",
        )


@pytest.mark.unit()
def test_notification_mark_sent_updates_state() -> None:
    notification = Notification.create(
        notification_type=NotificationType.PUSH,
        recipient="device:user-1",
        template_name="order_confirmed_push",
        subject="Confirmed",
        body="Body",
        aggregate_id="order-1",
        event_type="order-service.order.confirmed",
    )

    notification.mark_sent("push-1")

    assert notification.status == NotificationStatus.SENT
    assert notification.provider_message_id == "push-1"
    assert notification.sent_at is not None
