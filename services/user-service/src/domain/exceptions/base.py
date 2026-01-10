"""
Domain exceptions - business errors that can occur in the domain layer.

Principles:
1. Exceptions should be part of ubiquitous language
2. Should not contain technical details (SQL, HTTP, etc.)
3. Should be understandable by business
"""

from typing import Any


class DomainError(Exception):
    """
    Base class for all domain errors.

    Inherit from Exception for type safety:
    we can catch only domain errors with except DomainError.

    Attributes:
        message: Human-readable error message
        details: Additional details (optional)
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """String representation for logging."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class UserAlreadyExistsError(DomainError):
    """
    User with this email already exists.

    Used in RegisterUserUseCase when attempting to create a duplicate.
    """

    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"User with email '{email}' already exists",
            details={"email": email},
        )


class UserNotFoundError(DomainError):
    """
    User not found.

    Used in use cases when attempting to get a non-existent user.
    """

    def __init__(self, user_id: str | None = None, email: str | None = None) -> None:
        if user_id:
            message = f"User with id '{user_id}' not found"
            details = {"user_id": user_id}
        elif email:
            message = f"User with email '{email}' not found"
            details = {"email": email}
        else:
            message = "User not found"
            details = {}

        super().__init__(message=message, details=details)


class InvalidEmailError(DomainError):
    """
    Email address is invalid.

    Usually not needed since Email Value Object validates itself,
    but useful for explicit error handling.
    """

    def __init__(self, email: str, reason: str | None = None) -> None:
        message = f"Invalid email format: '{email}'"
        if reason:
            message += f" - {reason}"

        super().__init__(message=message, details={"email": email, "reason": reason})


class InvalidPasswordError(DomainError):
    """
    Password does not meet business rules.

    Used when Password Value Object validation fails.
    """

    def __init__(self, reason: str | None = None) -> None:
        message = "Invalid password"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason})


class InvalidProfileError(DomainError):
    """
    User profile data does not meet business rules.
    """

    def __init__(self, reason: str | None = None) -> None:
        message = "Invalid profile data"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason})


class InvalidCredentialsError(DomainError):
    """
    Authentication failed due to invalid credentials.

    Used in LoginUserUseCase to avoid leaking whether email or password is wrong.
    """

    def __init__(self) -> None:
        super().__init__(message="Invalid credentials", details={})


class InvalidTokenError(DomainError):
    """
    Token is invalid or expired.

    Used in refresh flow and auth dependencies when JWT validation fails.
    """

    def __init__(self, reason: str | None = None) -> None:
        message = "Invalid or expired token"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason} if reason else {})


class PermissionDeniedError(DomainError):
    """
    User does not have required permissions.
    """

    def __init__(self, reason: str | None = None) -> None:
        message = "Insufficient permissions"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, details={"reason": reason} if reason else {})
