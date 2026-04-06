from __future__ import annotations

from typing import Literal

from shared.events.base import BaseEvent


class NotificationEmailSentEvent(BaseEvent):
    """Notification email sent event."""

    event_type: Literal[
        "notification-service.notification.email_sent"
    ] = "notification-service.notification.email_sent"
    aggregate_type: Literal["notification"] = "notification"

    notification_type: str
    recipient: str
    template_name: str
    source_event_type: str


class NotificationPushSentEvent(BaseEvent):
    """Notification push sent event."""

    event_type: Literal[
        "notification-service.notification.push_sent"
    ] = "notification-service.notification.push_sent"
    aggregate_type: Literal["notification"] = "notification"

    notification_type: str
    recipient: str
    template_name: str
    source_event_type: str
