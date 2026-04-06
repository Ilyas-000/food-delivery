"""In-memory notification repository."""

from uuid import UUID

from src.application.interfaces.notification_repository import INotificationRepository
from src.domain.entities.notification import Notification


class InMemoryNotificationRepository(INotificationRepository):
    """Store notifications in memory for current phase."""

    def __init__(self) -> None:
        self._storage: dict[UUID, Notification] = {}

    async def save(self, notification: Notification) -> Notification:
        """Persist notification."""
        self._storage[notification.id] = notification
        return notification

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        """Fetch notification by identifier."""
        return self._storage.get(notification_id)

    async def list_all(self) -> list[Notification]:
        """Return notifications ordered by creation time descending."""
        return sorted(
            self._storage.values(),
            key=lambda notification: notification.created_at,
            reverse=True,
        )

    def clear(self) -> None:
        """Reset repository state."""
        self._storage.clear()
