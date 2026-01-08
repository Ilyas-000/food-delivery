"""
IPasswordHasher - interface for password hashing operations.

Security best practices (для собеседований):
1. НИКОГДА не храним plain text пароли
2. Используем bcrypt (или argon2) - устойчивы к rainbow tables
3. Bcrypt автоматически добавляет соль (salt)
4. Bcrypt медленный - это feature, защита от brute force

Interview questions:
Q: "Почему bcrypt, а не SHA256?"
A: SHA256 быстрый - можно брутфорсить GPU
   bcrypt медленный + адаптивный (можно увеличить rounds)

Q: "Что такое соль (salt)?"
A: Случайные данные, добавляемые к паролю перед хэшированием
   Защита от rainbow tables (предвычисленных хэшей)
"""

from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    """
    Interface for password hashing and verification.

    Encapsulates password security logic.
    Implementation может использовать bcrypt, argon2, scrypt.

    Methods:
    - hash_password() - хэшировать plain text пароль
    - verify_password() - проверить пароль против хэша
    """

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
