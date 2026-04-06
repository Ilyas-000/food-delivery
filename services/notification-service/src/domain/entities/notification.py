"""Notification domain entity."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.exceptions.notification import NotificationValidationError
from src.domain.value_objects.notification_status import NotificationStatus
from src.domain.value_objects.notification_type import NotificationType


@dataclass
class Notification:
    """Notification aggregate."""

    id: UUID
    notification_type: NotificationType
    recipient: str
    template_name: str
    subject: str
    body: str
    status: NotificationStatus
    aggregate_id: str
    event_type: str
    user_id: str | None
    created_at: datetime
    sent_at: datetime | None = None
    provider_message_id: str | None = None
    error_message: str | None = None

    @classmethod
    def create(
        cls,
        *,
        notification_type: NotificationType,
        recipient: str,
        template_name: str,
        subject: str,
        body: str,
        aggregate_id: str,
        event_type: str,
        user_id: str | None = None,
    ) -> "Notification":
        """Create notification with validation."""
        cleaned_recipient = recipient.strip()
        cleaned_subject = subject.strip()
        cleaned_body = body.strip()
        cleaned_template_name = template_name.strip()
        cleaned_aggregate_id = aggregate_id.strip()
        cleaned_event_type = event_type.strip()

        if not cleaned_recipient:
            raise NotificationValidationError("notification recipient is required")
        if not cleaned_subject:
            raise NotificationValidationError("notification subject is required")
        if not cleaned_body:
            raise NotificationValidationError("notification body is required")
        if not cleaned_template_name:
            raise NotificationValidationError("template_name is required")
        if not cleaned_aggregate_id:
            raise NotificationValidationError("aggregate_id is required")
        if not cleaned_event_type:
            raise NotificationValidationError("event_type is required")

        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            notification_type=notification_type,
            recipient=cleaned_recipient,
            template_name=cleaned_template_name,
            subject=cleaned_subject,
            body=cleaned_body,
            status=NotificationStatus.PENDING,
            aggregate_id=cleaned_aggregate_id,
            event_type=cleaned_event_type,
            user_id=user_id,
            created_at=now,
        )

    def mark_sent(self, provider_message_id: str) -> None:
        """Mark notification as delivered."""
        cleaned_provider_message_id = provider_message_id.strip()
        if not cleaned_provider_message_id:
            raise NotificationValidationError("provider_message_id is required")

        self.status = NotificationStatus.SENT
        self.provider_message_id = cleaned_provider_message_id
        self.error_message = None
        self.sent_at = datetime.now(UTC)

    def mark_failed(self, reason: str) -> None:
        """Mark notification as failed."""
        cleaned_reason = reason.strip()
        if not cleaned_reason:
            raise NotificationValidationError("failure reason is required")

        self.status = NotificationStatus.FAILED
        self.error_message = cleaned_reason
        self.sent_at = datetime.now(UTC)
