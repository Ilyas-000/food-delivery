"""
IRefreshTokenRepository - interface for refresh token storage.

Stores active refresh token JTIs (whitelist) for rotation and logout.
"""

from abc import ABC, abstractmethod
from uuid import UUID


class IRefreshTokenRepository(ABC):
    """Interface for managing refresh token JTIs."""

    @abstractmethod
    async def store(self, jti: str, user_id: UUID, expires_in: int) -> None:
        """
        Store refresh token JTI as active.

        Args:
            jti: Unique token identifier
            user_id: User UUID for reference/audit
            expires_in: TTL in seconds
        """

    @abstractmethod
    async def exists(self, jti: str) -> bool:
        """
        Check if refresh token JTI is active.

        Args:
            jti: Token identifier
        """

    @abstractmethod
    async def delete(self, jti: str) -> None:
        """
        Revoke refresh token JTI.

        Args:
            jti: Token identifier
        """
