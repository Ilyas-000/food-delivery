"""
PasswordHasher - bcrypt implementation for password hashing.

Uses bcrypt для безопасного хэширования паролей.

Why bcrypt (для собеседований):
1. Slow by design - защита от brute force
2. Adaptive - можно увеличивать rounds со временем
3. Built-in salt - защита от rainbow tables
4. Industry standard - используется повсеместно

Security parameters:
- rounds=12 (default) - ~300ms на хэш (баланс security/performance)
- Можно увеличить до 14-16 для более критичных систем

Interview notes:
Q: "Можно ли использовать hashlib (SHA256)?"
A: Нет! SHA256 слишком быстрый, можно брутфорсить GPU
   Нужны key derivation functions: bcrypt, argon2, scrypt

Q: "Что если в будущем нужно сменить алгоритм?"
A: Храним версию в хэше ($2b$ - bcrypt)
   При логине проверяем версию и перехэшируем
"""

import asyncio
from typing import cast

import bcrypt

from src.application.interfaces.password_hasher import IPasswordHasher


class PasswordHasher(IPasswordHasher):
    """
    Bcrypt implementation of IPasswordHasher.

    Bcrypt - это slow hashing algorithm, специально разработанный для паролей.
    Он использует Blowfish cipher и адаптивное количество раундов.

    Attributes:
        rounds: Количество раундов хэширования (по умолчанию 12)
                Больше rounds = безопаснее, но медленнее
                12 rounds ≈ 300ms (хороший баланс)
    """

    MIN_BCRYPT_ROUNDS = 4
    MAX_BCRYPT_ROUNDS = 31
    MAX_PASSWORD_BYTES = 72

    def __init__(self, rounds: int = 12) -> None:
        """
        Initialize password hasher.

        Args:
            rounds: Number of bcrypt rounds (4-31, рекомендуется 12-14)
        """
        if not self.MIN_BCRYPT_ROUNDS <= rounds <= self.MAX_BCRYPT_ROUNDS:
            raise ValueError(
                f"Bcrypt rounds must be between {self.MIN_BCRYPT_ROUNDS} "
                f"and {self.MAX_BCRYPT_ROUNDS}"
            )

        self._rounds = rounds

    async def hash_password(self, plain_password: str) -> str:
        """
        Hash password using bcrypt.

        Bcrypt - CPU-intensive операция, блокирует event loop.
        Поэтому запускаем в thread pool через asyncio.to_thread().

        IMPORTANT: Business validation (min length, complexity) should be done
        in Domain layer (Password Value Object) before calling this method.
        This method only enforces technical constraints (bcrypt limitations).

        Args:
            plain_password: Plain text password (already validated by domain layer)

        Returns:
            str: Bcrypt hash (format: $2b$12$salthash...)

        Raises:
            ValueError: If password exceeds bcrypt technical limitations

        Technical constraints:
        - Maximum 72 bytes (bcrypt limitation)

        Example:
            # Domain layer validation first
            password = Password("MyPassword123!")  # validates business rules
            # Then hash
            hasher = PasswordHasher(rounds=12)
            hashed = await hasher.hash_password(password.value)
            # hashed: "$2b$12$KIXx..."
        """
        # Базовая проверка
        if not plain_password:
            raise ValueError("Password cannot be empty")

        # Bcrypt technical limitation: максимум 72 байта
        if len(plain_password) > self.MAX_PASSWORD_BYTES:
            raise ValueError("Password too long (maximum 72 characters for bcrypt)")

        # Преобразуем в bytes
        password_bytes = plain_password.encode("utf-8")

        # Generate salt and hash
        # bcrypt.hashpw() - blocking call, запускаем в thread pool
        salt = bcrypt.gensalt(rounds=self._rounds)
        hash_bytes = cast(
            bytes,
            await asyncio.to_thread(bcrypt.hashpw, password_bytes, salt),
        )

        # Возвращаем как string
        return hash_bytes.decode("utf-8")

    async def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """
        Verify password against bcrypt hash.

        Constant-time comparison для защиты от timing attacks.
        bcrypt.checkpw() использует constant-time comparison internally.

        Args:
            plain_password: Password to verify
            password_hash: Stored bcrypt hash

        Returns:
            bool: True if password matches

        Example:
            hasher = PasswordHasher()
            is_valid = await hasher.verify_password(
                "MyPassword123!",
                "$2b$12$KIXx..."
            )
        """
        if not plain_password or not password_hash:
            return False

        try:
            password_bytes = plain_password.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")

            # bcrypt.checkpw() - blocking call, запускаем в thread pool
            result = await asyncio.to_thread(bcrypt.checkpw, password_bytes, hash_bytes)

            return bool(result)

        except (ValueError, AttributeError):
            # Невалидный хэш или encoding error
            return False
