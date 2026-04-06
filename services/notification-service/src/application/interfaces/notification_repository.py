"""Repository contract for notifications."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.notification import Notification


class INotificationRepository(ABC):
    """Notification persistence contract."""

    @abstractmethod
    async def save(self, notification: Notification) -> Notification:
        """Persist a notification."""

    @abstractmethod
    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        """Fetch a notification by identifier."""

    @abstractmethod
    async def list_all(self) -> list[Notification]:
        """Return all notifications ordered by creation time."""
