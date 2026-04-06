"""Notification API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.dto.notification import NotificationListResponseDTO, NotificationResponseDTO


class SendEmailRequest(BaseModel):
    """Request schema for manual email delivery."""

    recipient: str = Field(min_length=1)
    template_name: str = Field(min_length=1)
    template_context: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: str = Field(min_length=1)
    event_type: str = "manual.email.requested"
    user_id: str | None = None


class SendPushRequest(BaseModel):
    """Request schema for manual push delivery."""

    recipient: str = Field(min_length=1)
    template_name: str = Field(min_length=1)
    template_context: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: str = Field(min_length=1)
    event_type: str = "manual.push.requested"
    user_id: str | None = None


class NotificationResponse(BaseModel):
    """Response schema for notification state."""

    notification_id: UUID
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
    def from_dto(cls, dto: NotificationResponseDTO) -> "NotificationResponse":
        """Build API response from DTO."""
        return cls(
            notification_id=dto.id,
            notification_type=dto.notification_type,
            recipient=dto.recipient,
            template_name=dto.template_name,
            subject=dto.subject,
            body=dto.body,
            status=dto.status,
            aggregate_id=dto.aggregate_id,
            event_type=dto.event_type,
            user_id=dto.user_id,
            provider_message_id=dto.provider_message_id,
            error_message=dto.error_message,
            created_at=dto.created_at,
            sent_at=dto.sent_at,
        )


class NotificationListResponse(BaseModel):
    """Response schema for notification history."""

    items: list[NotificationResponse]
    total: int

    @classmethod
    def from_dto(cls, dto: NotificationListResponseDTO) -> "NotificationListResponse":
        """Build history response from DTO."""
        return cls(
            items=[NotificationResponse.from_dto(item) for item in dto.items],
            total=dto.total,
        )
