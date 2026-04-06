"""Get notification use case."""

from uuid import UUID

from src.application.dto.notification import NotificationResponseDTO
from src.application.interfaces.notification_repository import INotificationRepository
from src.domain.exceptions.notification import NotificationNotFoundError


class GetNotificationUseCase:
    """Fetch a single notification."""

    def __init__(self, repository: INotificationRepository) -> None:
        self._repository = repository

    async def execute(self, notification_id: UUID) -> NotificationResponseDTO:
        """Return notification details."""
        notification = await self._repository.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError(f"notification '{notification_id}' not found")
        return NotificationResponseDTO.from_entity(notification)
