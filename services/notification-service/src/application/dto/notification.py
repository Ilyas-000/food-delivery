"""Notification application DTOs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities.notification import Notification


class RenderedNotificationDTO(BaseModel):
    """Rendered notification content."""

    subject: str
    body: str


class SendEmailDTO(BaseModel):
    """Input payload for email delivery."""

    recipient: str
    template_name: str
    template_context: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: str
    event_type: str
    user_id: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SendPushDTO(BaseModel):
    """Input payload for push delivery."""

    recipient: str
    template_name: str
    template_context: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: str
    event_type: str
    user_id: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NotificationResponseDTO(BaseModel):
    """Output DTO for notification state."""

    id: UUID
    notification_type: str
    recipient: str
    template_name: str
    subject: str
    body: str
    status: str
    aggregate_id: str
    event_type: str
    user_id: str | None = None
    provider_message_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    sent_at: datetime | None = None

    @classmethod
    def from_entity(cls, notification: Notification) -> "NotificationResponseDTO":
        """Build response DTO from domain entity."""
        return cls(
            id=notification.id,
            notification_type=notification.notification_type.value,
            recipient=notification.recipient,
            template_name=notification.template_name,
            subject=notification.subject,
            body=notification.body,
            status=notification.status.value,
            aggregate_id=notification.aggregate_id,
            event_type=notification.event_type,
            user_id=notification.user_id,
            provider_message_id=notification.provider_message_id,
            error_message=notification.error_message,
            created_at=notification.created_at,
            sent_at=notification.sent_at,
        )


class NotificationListResponseDTO(BaseModel):
    """Collection DTO for notification history."""

    items: list[NotificationResponseDTO]
    total: int
