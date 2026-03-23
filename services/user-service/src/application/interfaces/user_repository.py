"""Repository contract for user persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email


class IUserRepository(ABC):
    """Persistence boundary used by user application use cases."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Create a new user in the repository.

        Args:
            user: User entity to create

        Returns:
            User: Created user (может содержать дополнительные поля из БД)

        Raises:
            Exception: Infrastructure-specific errors (handled by implementation)

        Example:
            user = User.create(...)
            saved_user = await repository.create(user)
        """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User | None: User entity or None if not found

        Example:
            user = await repository.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError(user_id=str(user_id))
        """

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None:
        """
        Get user by email.

        Args:
            email: Email value object

        Returns:
            User | None: User entity or None if not found

        Example:
            email = Email("user@example.com")
            user = await repository.get_by_email(email)
        """

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """
        Check if user with this email exists.

        Optimization: faster than get_by_email() когда нужна только проверка.
        Можно реализовать через SELECT EXISTS в PostgreSQL.

        Args:
            email: Email value object

        Returns:
            bool: True if user exists

        Example:
            email = Email("user@example.com")
            if await repository.exists_by_email(email):
                raise UserAlreadyExistsError(str(email))
        """

    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update existing user.

        Args:
            user: User entity with updated fields

        Returns:
            User: Updated user

        Raises:
            Exception: If user not found or update fails

        Example:
            user.update_profile(full_name="New Name")
            updated_user = await repository.update(user)
        """

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """
        Delete user (soft delete recommended).

        В нашем случае лучше использовать soft delete (user.deactivate()),
        но интерфейс предоставляет опцию для hard delete.

        Args:
            user_id: User UUID

        Raises:
            Exception: If user not found

        Example:
            await repository.delete(user_id)
        """
