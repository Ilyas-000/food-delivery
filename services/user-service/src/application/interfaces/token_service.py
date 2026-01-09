"""
ITokenService - interface for JWT token operations.

Encapsulates token creation and decoding so application layer
doesn't depend on конкретной реализации (PyJWT, shared utils).
"""

from abc import ABC, abstractmethod
from typing import Any

from src.application.dto.auth import AuthTokensDTO
from src.domain.value_objects.user_role import UserRole


class ITokenService(ABC):
    """Interface for JWT token operations."""

    @abstractmethod
    def create_token_pair(
        self,
        subject: str,
        role: UserRole,
        extra_claims: dict[str, Any] | None = None,
    ) -> AuthTokensDTO:
        """
        Create access + refresh token pair.

        Args:
            subject: User ID (stored in "sub" claim)
            role: User role (used in access token claims)
            extra_claims: Optional extra claims (e.g., email)
        """

    @abstractmethod
    def decode_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            dict: Decoded payload

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
