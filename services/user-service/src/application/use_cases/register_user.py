"""Use case for user registration."""

import structlog

from src.application.dto.auth import RegisterUserDTO
from src.application.dto.user import UserResponseDTO
from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.user_repository import IUserRepository
from src.domain.entities.user import User
from src.domain.exceptions.base import (
    InvalidEmailError,
    InvalidPasswordError,
    UserAlreadyExistsError,
)
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password

# Structured logging
logger = structlog.get_logger(__name__)


class RegisterUserUseCase:
    """Validate input, create user entity, and persist new user."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
    ) -> None:
        """
        Initialize use case with dependencies.

        Dependency Injection через конструктор - классический паттерн.
        В production используем DI containers (dependency-injector, punq).

        Args:
            user_repository: Repository для работы с пользователями
            password_hasher: Service для хэширования паролей
        """
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def execute(self, dto: RegisterUserDTO) -> UserResponseDTO:
        """
        Execute user registration use case.

        Главный метод use case - execute().
        Часто используется паттерн Command - один метод execute().

        Args:
            dto: Registration data

        Returns:
            UserResponseDTO: Created user data (without password!)

        Raises:
            UserAlreadyExistsError: If user with this email exists
            InvalidEmailError: If email format is invalid (from Email VO)
            ValueError: If other validation fails

        Example:
            dto = RegisterUserDTO(
                email="user@example.com",
                password="SecurePass123!",
                full_name="John Doe"
            )
            result = await use_case.execute(dto)
            # result.id - UUID нового пользователя
        """
        logger.info("register_user.started", email=dto.email)

        # Step 1: Create Email Value Object (validates format)
        # Если email невалиден - Email.__init__ выбросит ValueError
        # Конвертируем в domain exception для консистентности
        try:
            email = Email(dto.email)
        except ValueError as e:
            logger.warning("register_user.invalid_email", email=dto.email, error=str(e))
            # Convert ValueError to domain exception InvalidEmailError
            # Это даст консистентную обработку ошибок на уровне API
            raise InvalidEmailError(dto.email, reason=str(e)) from e

        # Step 2: Create Password Value Object (validates business rules)
        # Domain layer validates: min/max length, complexity requirements
        try:
            password = Password(dto.password)
        except ValueError as e:
            logger.warning("register_user.invalid_password", error=str(e))
            raise InvalidPasswordError(str(e)) from e

        # Step 3: Check if user already exists
        # Используем exists_by_email() - оптимизация, не загружаем весь объект
        if await self._user_repository.exists_by_email(email):
            logger.warning("register_user.already_exists", email=str(email))
            raise UserAlreadyExistsError(str(email))

        # Step 4: Hash password
        # НИКОГДА не храним plain text пароли!
        # password_hasher использует bcrypt с солью
        # Pass the validated plain text value to hasher
        password_hash = await self._password_hasher.hash_password(password.value)

        # Step 5: Create User entity (через factory method)
        # Domain logic - валидация, генерация ID, timestamps
        user = User.create(
            email=email,
            password_hash=password_hash,
            full_name=dto.full_name,
            role=dto.role,
            phone=dto.phone,
        )

        # Step 6: Save to repository
        # Repository реализация может добавить дополнительные поля (например, DB-generated)
        # IntegrityError (duplicate email) маппится в UserAlreadyExistsError внутри repository.
        created_user = await self._user_repository.create(user)

        logger.info(
            "register_user.success",
            user_id=str(created_user.id),
            email=str(created_user.email),
            role=created_user.role.value,
        )

        # Step 7: Convert to DTO (скрываем password_hash!)
        # DTO - контракт с внешним миром, entity - внутренняя модель
        return UserResponseDTO.from_entity(created_user)
