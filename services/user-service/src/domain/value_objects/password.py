"""
Password - Value Object for plain text password with validation.

IMPORTANT: This Value Object is for PLAIN TEXT passwords (before hashing).
It validates business rules for password strength.

After validation, the password is hashed by IPasswordHasher and stored as password_hash.

Value Object advantages:
1. Single place for password validation rules
2. Type safety (Password instead of str)
3. Impossible to create invalid password
4. Business rules expressed in domain layer

Architecture:
- Domain Layer (Password VO): Business rules (min length, complexity)
- Infrastructure (PasswordHasher): Technical implementation (bcrypt, hashing)
"""

from dataclasses import dataclass

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 72


@dataclass(frozen=True)  # Immutable for security
class Password:
    """
    Password Value Object with business validation rules.

    Business Rules (as of 2024):
    - Minimum 8 characters (security best practice)
    - Maximum 72 characters (bcrypt technical limitation)
    - At least one letter (optional, can be extended)

    Note: This is for PLAIN TEXT password validation only.
    After validation, password is hashed and Password VO is discarded.

    Attributes:
        value: Plain text password (NEVER store this in DB!)

    Raises:
        ValueError: If password doesn't meet business rules

    Examples:
        >>> password = Password("SecurePass123!")
        >>> str(password)  # Returns value (be careful with logging!)
        'SecurePass123!'

        >>> Password("weak")  # Raises ValueError
    """

    value: str

    def __post_init__(self) -> None:
        """
        Validate password against business rules.

        This runs after __init__ (dataclass feature).
        """
        # Strip whitespace (passwords shouldn't have leading/trailing spaces)
        stripped = self.value.strip()

        # Business rule: minimum length
        if len(stripped) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")

        # Business rule: maximum length (bcrypt limitation)
        if len(stripped) > MAX_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must not exceed {MAX_PASSWORD_LENGTH} characters (bcrypt limitation)"
            )

        # Business rule: must contain at least one letter
        # (prevents purely numeric passwords like "12345678")
        if not any(c.isalpha() for c in stripped):
            raise ValueError("Password must contain at least one letter")

        # Store stripped value
        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(self, "value", stripped)

    def __str__(self) -> str:
        """
        String representation.

        WARNING: Be careful with logging! This returns plain text password.
        Consider masking in production logs.
        """
        return self.value

    def __repr__(self) -> str:
        """
        Developer representation.

        Masks the password value for security (in logs, debugger, etc).
        """
        return "Password(***masked***)"
