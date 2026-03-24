"""Password hashing interface for application layer."""

from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """Contract for hashing and verifying passwords."""

    @abstractmethod
    async def hash_password(self, plain_password: str) -> str:
        """
        Hash a plain text password.

        Args:
            plain_password: Plain text password from user

        Returns:
            str: Hashed password (bcrypt format: $2b$12$...)

        Example:
            hashed = await hasher.hash_password("MySecurePass123!")
            # hashed: "$2b$12$KIXxLfE4..."
        """

    @abstractmethod
    async def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Password to check
            password_hash: Stored hash from database

        Returns:
            bool: True if password matches

        Example:
            is_valid = await hasher.verify_password(
                "MySecurePass123!",
                "$2b$12$KIXxLfE4..."
            )
        """
