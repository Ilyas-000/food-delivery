"""
UpdateUserProfileUseCase - business logic for updating user profile.
"""

import structlog

from src.application.dto.user import UpdateUserProfileDTO, UserResponseDTO
from src.application.interfaces.user_repository import IUserRepository
from src.domain.exceptions.base import InvalidProfileError, UserNotFoundError

logger = structlog.get_logger(__name__)


class UpdateUserProfileUseCase:
    """Use case for updating user profile fields."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, dto: UpdateUserProfileDTO) -> UserResponseDTO:
        """Update user profile fields."""
        logger.info("update_user_profile.started", user_id=str(dto.user_id))

        if dto.full_name is None and dto.phone is None:
            raise InvalidProfileError("No fields provided for update")

        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None or not user.is_active:
            logger.warning("update_user_profile.not_found", user_id=str(dto.user_id))
            raise UserNotFoundError(user_id=str(dto.user_id))

        try:
            user.update_profile(full_name=dto.full_name, phone=dto.phone)
        except ValueError as exc:
            logger.warning(
                "update_user_profile.invalid_data",
                user_id=str(dto.user_id),
                error=str(exc),
            )
            raise InvalidProfileError(str(exc)) from exc

        updated = await self._user_repository.update(user)

        logger.info("update_user_profile.success", user_id=str(updated.id))
        return UserResponseDTO.from_entity(updated)
