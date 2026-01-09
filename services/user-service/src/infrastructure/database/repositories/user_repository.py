"""
UserRepository - SQLAlchemy implementation of IUserRepository.

Repository Pattern implementation (популярно на собеседованиях):

Repository Pattern:
- Абстрагирует доступ к данным
- Делает маппинг между Domain Entities и ORM Models
- Инкапсулирует queries и database logic
- Легко тестировать (можно создать mock/in-memory implementation)

Key responsibilities:
1. CRUD operations
2. Entity ↔ Model mapping
3. Database error handling
4. Query optimization

Interview questions:
Q: "Почему не использовать SQLAlchemy напрямую в use cases?"
A: Нарушает Dependency Inversion Principle
   Use cases зависели бы от concrete implementation
   Сложно тестировать (нужна реальная БД)
   Coupling между business logic и persistence

Q: "Где происходит валидация?"
A: В Domain Entity (бизнес-правила)
   Repository просто сохраняет/загружает
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.application.interfaces.user_repository import IUserRepository
from src.domain.entities.user import User
from src.domain.exceptions.base import UserAlreadyExistsError
from src.domain.value_objects.email import Email
from src.infrastructure.database.models.user_model import UserModel

logger = structlog.get_logger(__name__)


class UserRepository(IUserRepository):
    """
    SQLAlchemy implementation of IUserRepository.

    Реализует Repository Pattern для работы с пользователями.

    Architecture:
    - Принимает Domain Entity (User)
    - Конвертирует в ORM Model (UserModel)
    - Сохраняет в PostgreSQL
    - При загрузке конвертирует обратно Model → Entity

    Dependencies:
    - session: AsyncSession (SQLAlchemy async session)

    Note: Repository НЕ знает откуда взялась session (DI)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session (injected)
        """
        self._session = session

    async def create(self, user: User) -> User:
        """
        Create new user in database.

        Flow:
        1. Convert Entity → Model
        2. Add to session
        3. Commit transaction
        4. Convert Model → Entity
        5. Return Entity

        Args:
            user: User domain entity

        Returns:
            User: Created user entity

        Raises:
            Exception: If database error occurs (e.g., unique constraint)

        Example:
            user = User.create(...)
            saved_user = await repository.create(user)
        """
        logger.info("repository.create_user.started", user_id=str(user.id))

        # Entity → Model mapping
        user_model = self._entity_to_model(user)

        try:
            # Add to session and commit
            self._session.add(user_model)
            await self._session.commit()
            await self._session.refresh(user_model)  # Get DB-generated fields

            logger.info("repository.create_user.success", user_id=str(user.id))

            # Model → Entity mapping
            return self._model_to_entity(user_model)

        except IntegrityError as e:
            # Unique constraint violation (e.g., duplicate email)
            await self._session.rollback()
            logger.exception(
                "repository.create_user.integrity_error",
                user_id=str(user.id),
                error=str(e),
            )
            raise UserAlreadyExistsError(str(user.email)) from e

        except Exception as e:
            # Other database errors
            await self._session.rollback()
            logger.exception("repository.create_user.error", user_id=str(user.id), error=str(e))
            raise

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Get user by ID.

        Uses SQLAlchemy 2.0 async select() style.

        Args:
            user_id: User UUID

        Returns:
            User | None: User entity or None if not found

        Example:
            user = await repository.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError(...)
        """
        logger.debug("repository.get_user_by_id", user_id=str(user_id))

        # SQLAlchemy 2.0 style query
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if user_model is None:
            logger.debug("repository.get_user_by_id.not_found", user_id=str(user_id))
            return None

        # Model → Entity
        return self._model_to_entity(user_model)

    async def get_by_email(self, email: Email) -> User | None:
        """
        Get user by email.

        Email is indexed in DB for fast lookup (O(log n)).

        Args:
            email: Email value object

        Returns:
            User | None: User entity or None if not found

        Example:
            email = Email("user@example.com")
            user = await repository.get_by_email(email)
        """
        logger.debug("repository.get_user_by_email", email=str(email))

        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self._session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if user_model is None:
            logger.debug("repository.get_user_by_email.not_found", email=str(email))
            return None

        return self._model_to_entity(user_model)

    async def exists_by_email(self, email: Email) -> bool:
        """
        Check if user with email exists.

        Optimization: использует EXISTS query вместо загрузки всего объекта.
        EXISTS быстрее чем SELECT * когда нужна только проверка.

        Args:
            email: Email value object

        Returns:
            bool: True if user exists

        Example:
            if await repository.exists_by_email(email):
                raise UserAlreadyExistsError(...)
        """
        logger.debug("repository.exists_by_email", email=str(email))

        # SELECT EXISTS(...) query
        stmt = select(UserModel.id).where(UserModel.email == str(email)).limit(1)
        result = await self._session.execute(stmt)
        exists = result.scalar_one_or_none() is not None

        logger.debug("repository.exists_by_email.result", email=str(email), exists=exists)
        return exists

    async def update(self, user: User) -> User:
        """
        Update existing user.

        Explicitly checks if user exists before updating.
        This is safer than merge() which can silently create if not found.

        Args:
            user: User entity with updated fields

        Returns:
            User: Updated user entity

        Raises:
            ValueError: If user not found (explicit error)
            Exception: If update fails

        Example:
            user.update_profile(full_name="New Name")
            updated = await repository.update(user)
        """
        logger.info("repository.update_user.started", user_id=str(user.id))

        # Step 1: Load existing user from DB
        # This ensures user exists (explicit check)
        existing_model = await self._session.get(UserModel, user.id)

        if existing_model is None:
            logger.warning("repository.update_user.not_found", user_id=str(user.id))
            raise ValueError(f"User with id {user.id} not found")

        try:
            # Step 2: Update fields from entity
            # Explicit field-by-field update (clearer than merge)
            existing_model.email = str(user.email)
            existing_model.password_hash = user.password_hash
            existing_model.full_name = user.full_name
            existing_model.role = user.role
            existing_model.is_active = user.is_active
            existing_model.phone = user.phone
            existing_model.updated_at = user.updated_at

            # Step 3: Commit changes
            await self._session.commit()
            await self._session.refresh(existing_model)

            logger.info("repository.update_user.success", user_id=str(user.id))

            return self._model_to_entity(existing_model)

        except Exception as e:
            await self._session.rollback()
            logger.exception("repository.update_user.error", user_id=str(user.id), error=str(e))
            raise

    async def delete(self, user_id: UUID) -> None:
        """
        Delete user (hard delete).

        Note: В нашем проекте рекомендуется использовать soft delete
        (user.deactivate() + update()), но метод предоставлен для полноты.

        Args:
            user_id: User UUID

        Raises:
            Exception: If user not found

        Example:
            await repository.delete(user_id)
        """
        logger.info("repository.delete_user.started", user_id=str(user_id))

        user_model = await self._session.get(UserModel, user_id)

        if user_model is None:
            logger.warning("repository.delete_user.not_found", user_id=str(user_id))
            raise ValueError(f"User with id {user_id} not found")

        try:
            await self._session.delete(user_model)
            await self._session.commit()

            logger.info("repository.delete_user.success", user_id=str(user_id))

        except Exception as e:
            await self._session.rollback()
            logger.exception("repository.delete_user.error", user_id=str(user_id), error=str(e))
            raise

    # Private mapping methods

    def _entity_to_model(self, user: User) -> UserModel:
        """
        Convert Domain Entity to ORM Model.

        Mapping layer - преобразует чистую domain entity в SQLAlchemy model.

        Args:
            user: Domain entity

        Returns:
            UserModel: ORM model

        Note: Email Value Object → str, UserRole → enum
        """
        return UserModel(
            id=user.id,
            email=str(user.email),  # Email VO → str
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role,  # UserRole enum остаётся как есть
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _model_to_entity(self, model: UserModel) -> User:
        """
        Convert ORM Model to Domain Entity.

        Reverse mapping - из БД в domain.

        Args:
            model: ORM model

        Returns:
            User: Domain entity

        Note: str → Email Value Object
        """
        return User(
            id=model.id,
            email=Email(model.email),  # str → Email VO
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=model.role,
            is_active=model.is_active,
            phone=model.phone,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
