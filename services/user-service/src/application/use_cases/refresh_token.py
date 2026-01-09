"""
RefreshTokenUseCase - business logic for refresh token flow.

Flow:
1. Decode refresh token
2. Validate token type and subject
3. Load user by ID
4. Issue new token pair
"""

from uuid import UUID

import structlog

from src.application.dto.auth import AuthTokensDTO, RefreshTokenDTO
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.user_repository import IUserRepository
from src.domain.exceptions.base import InvalidTokenError

logger = structlog.get_logger(__name__)


class RefreshTokenUseCase:
    """Use case for refreshing JWT token pair."""

    def __init__(
        self,
        user_repository: IUserRepository,
        token_service: ITokenService,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service

    async def execute(self, dto: RefreshTokenDTO) -> AuthTokensDTO:
        """Validate refresh token and issue a new pair."""
        logger.info("refresh_token.started")

        payload = self._token_service.decode_token(dto.refresh_token)
        if payload.get("type") != "refresh":
            logger.warning("refresh_token.invalid_type", token_type=payload.get("type"))
            raise InvalidTokenError("Invalid token type")

        subject = payload.get("sub")
        if not subject:
            raise InvalidTokenError("Missing subject")

        try:
            user_id = UUID(str(subject))
        except ValueError as exc:
            raise InvalidTokenError("Invalid subject") from exc

        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("User not found or inactive")

        tokens = self._token_service.create_token_pair(
            subject=str(user.id),
            role=user.role,
        )

        logger.info("refresh_token.success", user_id=str(user.id))
        return tokens
