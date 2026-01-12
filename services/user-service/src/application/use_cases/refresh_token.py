"""
RefreshTokenUseCase - business logic for refresh token flow.

Flow:
1. Decode refresh token
2. Validate token type and JTI (whitelist)
3. Load user by ID
4. Revoke old JTI and issue new token pair
"""

from uuid import UUID, uuid4

import structlog

from src.application.dto.auth import AuthTokensDTO, RefreshTokenDTO
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
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
        refresh_token_repository: IRefreshTokenRepository,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service
        self._refresh_token_repository = refresh_token_repository

    async def execute(self, dto: RefreshTokenDTO) -> AuthTokensDTO:
        """Validate refresh token and issue a new pair."""
        logger.info("refresh_token.started")

        payload = self._token_service.decode_token(dto.refresh_token)
        if payload.get("type") != "refresh":
            logger.warning("refresh_token.invalid_type", token_type=payload.get("type"))
            raise InvalidTokenError("Invalid token type")

        jti = payload.get("jti")
        if not jti:
            raise InvalidTokenError("Missing jti")

        if not await self._refresh_token_repository.exists(jti):
            raise InvalidTokenError("Refresh token revoked")

        subject = payload.get("sub")
        if not subject:
            raise InvalidTokenError("Missing subject")

        try:
            user_id = UUID(str(subject))
        except ValueError as exc:
            raise InvalidTokenError("Invalid subject") from exc

        user = await self._user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            await self._refresh_token_repository.delete(jti)
            raise InvalidTokenError("User not found or inactive")

        await self._refresh_token_repository.delete(jti)

        new_jti = str(uuid4())
        tokens = self._token_service.create_token_pair(
            subject=str(user.id),
            role=user.role,
            extra_claims={"email": str(user.email)},
            refresh_claims={"jti": new_jti},
        )

        await self._refresh_token_repository.store(
            jti=new_jti,
            user_id=user.id,
            expires_in=tokens.refresh_expires_in,
        )

        logger.info("refresh_token.success", user_id=str(user.id))
        return tokens
