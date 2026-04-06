"""List notifications use case."""

from src.application.dto.notification import NotificationListResponseDTO, NotificationResponseDTO
from src.application.interfaces.notification_repository import INotificationRepository


class ListNotificationsUseCase:
    """Return notification history."""

    def __init__(self, repository: INotificationRepository) -> None:
        self._repository = repository

    async def execute(self) -> NotificationListResponseDTO:
        """Return all notifications."""
        notifications = await self._repository.list_all()
        items = [
            NotificationResponseDTO.from_entity(notification) for notification in notifications
        ]
        return NotificationListResponseDTO(items=items, total=len(items))
