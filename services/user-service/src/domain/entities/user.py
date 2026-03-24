"""User domain entity with profile and lifecycle operations."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
import uuid

from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

FULL_NAME_MIN_LEN = 2
FULL_NAME_MAX_LEN = 100
PHONE_MIN_LEN = 10
PHONE_MAX_LEN = 20
BCRYPT_HASH_LEN = 60
BCRYPT_HASH_PREFIXES = ("$2b$", "$2a$")


def _utc_now() -> datetime:
    """Helper для получения текущего времени в UTC."""
    return datetime.now(UTC)


@dataclass
class User:
    """
    User Entity - представляет пользователя в системе.

    Attributes:
        id: Уникальный идентификатор (UUID)
        email: Email пользователя (Value Object)
        password_hash: Хэш пароля (bcrypt), НИКОГДА не храним plain text
        full_name: Полное имя
        role: Роль пользователя (Customer, Courier, etc.)
        is_active: Активен ли пользователь (для soft delete)
        created_at: Время создания
        updated_at: Время последнего обновления

    Examples:
        >>> # Создание нового пользователя (через factory method)
        >>> user = User.create(
        ...     email=Email("user@example.com"),
        ...     password_hash="$2b$12$...",
        ...     full_name="John Doe",
        ...     role=UserRole.CUSTOMER
        ... )
        >>> user.id  # UUID автоматически сгенерирован
        >>> user.is_active  # True по умолчанию
    """

    # Обязательные поля
    id: uuid.UUID
    email: Email
    password_hash: str  # bcrypt hash
    full_name: str
    role: UserRole

    # Опциональные поля с дефолтами
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    # Metadata (опционально, для future расширений)
    phone: str | None = None

    @classmethod
    def create(
        cls,
        email: Email,
        password_hash: str,
        full_name: str,
        role: UserRole = UserRole.CUSTOMER,
        phone: str | None = None,
    ) -> "User":
        """
        Factory method для создания нового пользователя.

        Зачем factory method:
        1. Явный способ создания (User.create() vs User(...))
        2. Валидация бизнес-правил при создании
        3. Генерация ID и timestamps автоматически
        4. Возможность менять логику создания без изменения конструктора

        Args:
            email: Email пользователя (Value Object)
            password_hash: Хэш пароля (уже захэшированный bcrypt)
            full_name: Полное имя (2-100 characters)
            role: Роль пользователя (по умолчанию CUSTOMER)
            phone: Номер телефона (опционально, 10-20 characters if provided)

        Returns:
            User: Новый пользователь со сгенерированным ID

        Raises:
            ValueError: Если данные невалидны

        Business rules (Domain layer - single source of truth):
        - full_name: 2-100 characters (business requirement)
        - password_hash: must be valid bcrypt hash
        - phone: 10-20 characters if provided (international formats)

        Examples:
            >>> email = Email("user@example.com")
            >>> user = User.create(
            ...     email=email,
            ...     password_hash="$2b$12$...",
            ...     full_name="John Doe"
            ... )
        """
        # Валидация бизнес-правил для full_name
        if not full_name or len(full_name.strip()) < FULL_NAME_MIN_LEN:
            raise ValueError(f"Full name must be at least {FULL_NAME_MIN_LEN} characters")

        if len(full_name.strip()) > FULL_NAME_MAX_LEN:
            raise ValueError(f"Full name must not exceed {FULL_NAME_MAX_LEN} characters")

        # Валидация password_hash
        if not password_hash:
            raise ValueError("Password hash is required")

        # Простая проверка что это похоже на bcrypt hash
        # Bcrypt hash format: $2b$12$... (60 characters)
        if not password_hash.startswith(BCRYPT_HASH_PREFIXES):
            raise ValueError("Invalid password hash format (expected bcrypt)")

        if len(password_hash) != BCRYPT_HASH_LEN:
            raise ValueError(
                f"Invalid password hash length (expected {BCRYPT_HASH_LEN} characters for bcrypt)"
            )

        # Валидация phone если предоставлен
        if phone is not None:
            phone_stripped = phone.strip()
            if len(phone_stripped) < PHONE_MIN_LEN:
                raise ValueError(f"Phone number too short (minimum {PHONE_MIN_LEN} characters)")
            if len(phone_stripped) > PHONE_MAX_LEN:
                raise ValueError(f"Phone number too long (maximum {PHONE_MAX_LEN} characters)")

        # Генерируем UUID v4
        user_id = uuid.uuid4()

        # Создаём пользователя
        return cls(
            id=user_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name.strip(),
            role=role,
            phone=phone,
            is_active=True,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    def update_profile(self, full_name: str | None = None, phone: str | None = None) -> None:
        """
        Update user profile information.

        Бизнес-метод для изменения профиля.
        Это Rich Domain Model - логика внутри entity, а не в service.

        Args:
            full_name: Новое имя (опционально, 2-100 characters)
            phone: Новый телефон (опционально, 10-20 characters)

        Raises:
            ValueError: Если данные невалидны
        """
        if full_name is not None:
            full_name_stripped = full_name.strip()
            if len(full_name_stripped) < FULL_NAME_MIN_LEN:
                raise ValueError(f"Full name must be at least {FULL_NAME_MIN_LEN} characters")
            if len(full_name_stripped) > FULL_NAME_MAX_LEN:
                raise ValueError(f"Full name must not exceed {FULL_NAME_MAX_LEN} characters")
            self.full_name = full_name_stripped

        if phone is not None:
            phone_stripped = phone.strip()
            if len(phone_stripped) < PHONE_MIN_LEN:
                raise ValueError(f"Phone number too short (minimum {PHONE_MIN_LEN} characters)")
            if len(phone_stripped) > PHONE_MAX_LEN:
                raise ValueError(f"Phone number too long (maximum {PHONE_MAX_LEN} characters)")
            self.phone = phone_stripped

        # Обновляем timestamp
        self.updated_at = _utc_now()

    def change_password(self, new_password_hash: str) -> None:
        """
        Change user password.

        Args:
            new_password_hash: Новый хэш пароля (уже захэшированный)

        Raises:
            ValueError: Если хэш пустой
        """
        if not new_password_hash:
            raise ValueError("Password hash is required")

        self.password_hash = new_password_hash
        self.updated_at = _utc_now()

    def deactivate(self) -> None:
        """
        Deactivate user (soft delete).

        Вместо удаления из БД, помечаем как неактивного.
        Это бизнес-правило: мы не теряем историю.
        """
        self.is_active = False
        self.updated_at = _utc_now()

    def activate(self) -> None:
        """Activate previously deactivated user."""
        self.is_active = True
        self.updated_at = _utc_now()

    def __eq__(self, other: Any) -> bool:
        """
        Equality check based on ID (Entity equality).

        Entities сравниваются по ID, НЕ по значениям полей!
        Два User с одинаковыми email/name но разными ID - это РАЗНЫЕ пользователи.

        This is key difference from Value Objects (which compare by value).
        """
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets/dicts."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"User(id={self.id}, email={self.email}, "
            f"role={self.role}, is_active={self.is_active})"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary (for serialization).

        Обычно не рекомендуется в чистом DDD, но удобно для:
        - Логирования
        - Тестирования
        - Временной сериализации

        В production лучше использовать DTOs для сериализации.

        Returns:
            dict: Dictionary representation (без password_hash!)
        """
        return {
            "id": str(self.id),
            "email": str(self.email),
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
