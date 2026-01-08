"""
UserModel - SQLAlchemy ORM model for users table.

ORM Model vs Domain Entity (важно для собеседований):

ORM Model (UserModel):
- Представляет таблицу в БД
- Знает о SQLAlchemy, колонках, индексах
- Простая структура данных
- Persistence concern

Domain Entity (User):
- Представляет бизнес-концепцию
- Не знает о БД
- Содержит бизнес-логику и методы
- Business concern

Repository Pattern связывает их:
UserModel <--(маппинг)--> User Entity

Interview questions:
Q: "Почему не использовать SQLAlchemy модели как domain entities?"
A: Нарушает separation of concerns
   Domain зависел бы от ORM framework
   Сложно тестировать без БД
   Active Record anti-pattern (entity знает как себя сохранить)
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.value_objects.user_role import UserRole
from src.infrastructure.database.base import Base


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class UserModel(Base):
    """
    SQLAlchemy model for users table.

    Используем SQLAlchemy 2.0 style с Mapped и mapped_column.

    Table structure:
    - id: UUID primary key
    - email: Unique, indexed
    - password_hash: Bcrypt hash
    - full_name: User's full name
    - role: Enum (customer, courier, restaurant_owner, admin)
    - is_active: Soft delete flag
    - phone: Optional phone number
    - created_at: Creation timestamp
    - updated_at: Update timestamp

    Indexes:
    - email (unique) - для быстрого поиска при логине
    - role - для фильтрации пользователей по роли
    - created_at - для сортировки

    Note: Мы НЕ используем эту модель в domain/application слоях!
    Она используется только в infrastructure (repository).
    """

    __tablename__ = "users"

    # Primary Key - UUID
    # UUID лучше чем auto-increment int:
    # - Глобально уникальные
    # - Можно генерировать на клиенте
    # - Безопаснее (не раскрываем количество пользователей)
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="User unique identifier",
    )

    # Email - unique, indexed
    # index=True для быстрого поиска (O(log n) вместо O(n))
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique, lowercase)",
    )

    # Password hash - НЕ plain text!
    # Длина 60 символов достаточно для bcrypt ($2b$12$...)
    password_hash: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        comment="Bcrypt password hash",
    )

    # Full name
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User full name",
    )

    # Role - Enum
    # Используем PostgreSQL ENUM type для type safety на уровне БД
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=True),
        nullable=False,
        index=True,  # Индекс для фильтрации по ролям
        comment="User role in the system",
    )

    # Soft delete flag
    # is_active=False вместо DELETE - сохраняем историю
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is user active (soft delete)",
    )

    # Optional phone
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="User phone number (optional)",
    )

    # Timestamps - всегда UTC!
    # Важно: в микросервисах всегда используем UTC, конвертируем в timezone на клиенте
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,  # Индекс для сортировки
        comment="Creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,  # Автоматически обновляется при UPDATE
        comment="Last update timestamp (UTC)",
    )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"<UserModel(id={self.id}, email={self.email}, "
            f"role={self.role}, is_active={self.is_active})>"
        )
