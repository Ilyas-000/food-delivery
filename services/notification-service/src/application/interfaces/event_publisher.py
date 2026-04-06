"""Contracts for notification domain event publishing."""

from abc import ABC, abstractmethod

from src.domain.entities.notification import Notification


class INotificationEventPublisher(ABC):
    """Notification event publisher contract."""

    @abstractmethod
    async def publish_email_sent(self, notification: Notification) -> None:
        """Publish email delivery event."""

    @abstractmethod
    async def publish_push_sent(self, notification: Notification) -> None:
        """Publish push delivery event."""
