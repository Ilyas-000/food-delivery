"""
GetUserProfileUseCase - business logic for fetching user profile.
"""

import structlog

from src.application.dto.user import GetUserProfileDTO, UserResponseDTO
from src.application.interfaces.user_repository import IUserRepository
from src.domain.exceptions.base import UserNotFoundError

logger = structlog.get_logger(__name__)


class GetUserProfileUseCase:
    """Use case for retrieving a user profile by ID."""

    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(self, dto: GetUserProfileDTO) -> UserResponseDTO:
        """Fetch user profile by id."""
        logger.info("get_user_profile.started", user_id=str(dto.user_id))

        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None or not user.is_active:
            logger.warning("get_user_profile.not_found", user_id=str(dto.user_id))
            raise UserNotFoundError(user_id=str(dto.user_id))

        logger.info("get_user_profile.success", user_id=str(user.id))
        return UserResponseDTO.from_entity(user)
