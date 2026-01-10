"""
LogoutUserUseCase - revoke refresh token JTI.
"""

import structlog

from src.application.dto.auth import LogoutUserDTO
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
from src.application.interfaces.token_service import ITokenService
from src.domain.exceptions.base import InvalidTokenError

logger = structlog.get_logger(__name__)


class LogoutUserUseCase:
    """Use case for revoking refresh tokens (logout)."""

    def __init__(
        self,
        token_service: ITokenService,
        refresh_token_repository: IRefreshTokenRepository,
    ) -> None:
        self._token_service = token_service
        self._refresh_token_repository = refresh_token_repository

    async def execute(self, dto: LogoutUserDTO) -> None:
        """Revoke refresh token JTI."""
        logger.info("logout_user.started")

        payload = self._token_service.decode_token(dto.refresh_token)
        if payload.get("type") != "refresh":
            logger.warning("logout_user.invalid_type", token_type=payload.get("type"))
            raise InvalidTokenError("Invalid token type")

        jti = payload.get("jti")
        if not jti:
            raise InvalidTokenError("Missing jti")

        if await self._refresh_token_repository.exists(jti):
            await self._refresh_token_repository.delete(jti)

        logger.info("logout_user.success")
