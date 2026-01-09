"""
TokenService - JWT implementation for authentication.

Uses shared JWT utilities to keep token format consistent across services.
"""

from typing import Any

import jwt

from shared.common.jwt import create_access_token, create_refresh_token, decode_token
from src.application.dto.auth import AuthTokensDTO
from src.application.interfaces.token_service import ITokenService
from src.domain.exceptions.base import InvalidTokenError
from src.domain.value_objects.user_role import UserRole


class TokenService(ITokenService):
    """JWT token service implementation."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expires_minutes: int,
        refresh_expires_days: int,
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expires_minutes = access_expires_minutes
        self._refresh_expires_days = refresh_expires_days

    def create_token_pair(
        self,
        subject: str,
        role: UserRole,
        extra_claims: dict[str, Any] | None = None,
    ) -> AuthTokensDTO:
        access_claims: dict[str, Any] = {"role": role.value}
        if extra_claims:
            access_claims.update(extra_claims)

        access_token = create_access_token(
            subject=subject,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expires_minutes=self._access_expires_minutes,
            extra_claims=access_claims,
        )
        refresh_token = create_refresh_token(
            subject=subject,
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expires_days=self._refresh_expires_days,
        )

        return AuthTokensDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",  # nosec B106
            access_expires_in=self._access_expires_minutes * 60,
            refresh_expires_in=self._refresh_expires_days * 24 * 60 * 60,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            return decode_token(
                token=token,
                secret_key=self._secret_key,
                algorithms=[self._algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise InvalidTokenError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError("Token invalid") from exc
