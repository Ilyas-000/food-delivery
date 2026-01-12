"""
LoginUserUseCase - business logic for user authentication.

Flow:
1. Validate email format
2. Load user by email
3. Verify password
4. Generate access + refresh tokens (with JTI)
5. Store refresh token JTI in Redis whitelist
"""

from uuid import uuid4

import structlog

from src.application.dto.auth import AuthTokensDTO, LoginUserDTO
from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.user_repository import IUserRepository
from src.domain.exceptions.base import InvalidCredentialsError, InvalidEmailError
from src.domain.value_objects.email import Email

logger = structlog.get_logger(__name__)


class LoginUserUseCase:
    """Use case for user login and token issuance."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        refresh_token_repository: IRefreshTokenRepository,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._refresh_token_repository = refresh_token_repository

    async def execute(self, dto: LoginUserDTO) -> AuthTokensDTO:
        """Authenticate user and return token pair."""
        logger.info("login_user.started", email=dto.email)

        try:
            email = Email(dto.email)
        except ValueError as exc:
            logger.warning("login_user.invalid_email", email=dto.email, error=str(exc))
            raise InvalidEmailError(dto.email, reason=str(exc)) from exc

        user = await self._user_repository.get_by_email(email)
        if user is None or not user.is_active:
            logger.warning("login_user.invalid_credentials", email=str(email))
            raise InvalidCredentialsError

        is_valid = await self._password_hasher.verify_password(dto.password, user.password_hash)
        if not is_valid:
            logger.warning("login_user.invalid_credentials", email=str(email))
            raise InvalidCredentialsError

        refresh_jti = str(uuid4())
        tokens = self._token_service.create_token_pair(
            subject=str(user.id),
            role=user.role,
            extra_claims={"email": str(user.email)},
            refresh_claims={"jti": refresh_jti},
        )

        await self._refresh_token_repository.store(
            jti=refresh_jti,
            user_id=user.id,
            expires_in=tokens.refresh_expires_in,
        )

        logger.info("login_user.success", user_id=str(user.id))
        return tokens
