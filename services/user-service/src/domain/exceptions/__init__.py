"""Domain exceptions public API."""

from src.domain.exceptions.base import (
    DomainError,
    InvalidEmailError,
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

__all__ = [
    "DomainError",
    "InvalidEmailError",
    "InvalidPasswordError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
]
