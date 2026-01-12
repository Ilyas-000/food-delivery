"""
Email - Value Object for email addresses with validation.

Value Object - это immutable объект, который представляет концепцию из domain.
Два Email объекта с одинаковым значением считаются равными.

Преимущества Value Object:
1. Валидация в одном месте
2. Типобезопасность (Email вместо str)
3. Выражение domain концепций
4. Невозможность создать невалидный email

Uses email-validator library for production-grade email validation.
This library handles complex RFC 5321/5322 rules properly.
"""

from dataclasses import dataclass
from typing import Any

from email_validator import EmailNotValidError, validate_email


@dataclass(frozen=True)  # frozen=True делает объект immutable
class Email:
    """
    Email Value Object с встроенной валидацией.

    Attributes:
        value: Нормализованное значение email (lowercase)

    Raises:
        ValueError: Если email невалиден

    Examples:
        >>> email = Email("user@example.com")
        >>> str(email)
        'user@example.com'
        >>> email.value
        'user@example.com'
        >>> Email("User@Example.COM")  # Нормализуется к lowercase
        Email(value='user@example.com')
        >>> Email("invalid")  # Raises ValueError
    """

    value: str

    def __post_init__(self) -> None:
        """
        Валидация и нормализация после создания объекта.

        Uses email-validator library for RFC-compliant validation.
        @dataclass создаёт __init__, но мы можем добавить логику в __post_init__.
        """
        # Validate and normalize using email-validator library
        # This handles complex cases like quoted strings, internationalized emails, etc.
        try:
            # validate_email returns EmailInfo with normalized email
            # Don't check DNS/MX records (too slow for registration)
            validated = validate_email(
                self.value,
                check_deliverability=False,
            )
            # Use normalized form (lowercase, ASCII if possible)
            normalized = validated.normalized.lower()

        except EmailNotValidError as e:
            # email-validator raises EmailNotValidError with detailed message
            raise ValueError(f"Invalid email format: {e!s}") from e

        # Используем object.__setattr__ потому что объект frozen
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        """String representation для логов и UI."""
        return self.value

    def __eq__(self, other: Any) -> bool:
        """
        Сравнение по значению (а не по ссылке).

        Value Objects сравниваются по значению:
        Email("test@example.com") == Email("test@example.com")  # True
        """
        if not isinstance(other, Email):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """
        Hash для использования в set/dict.

        Нужен потому что мы переопределили __eq__.
        """
        return hash(self.value)
