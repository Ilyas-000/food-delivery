"""
User Service Configuration.

Загружает настройки из переменных окружения с использованием pydantic-settings.
Все чувствительные данные (пароли, токены) должны передаваться через environment variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки User Service.

    Все параметры загружаются из переменных окружения.
    Используется prefix "USER_SERVICE_" для избежания конфликтов с другими сервисами.
    """

    model_config = SettingsConfigDict(
        env_prefix="USER_SERVICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Игнорируем лишние переменные окружения
    )

    # Service Configuration
    service_name: str = Field(default="user-service", description="Service name for logging")
    environment: str = Field(
        default="development", description="Environment: development, staging, production"
    )
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")  # nosec B104
    api_port: int = Field(default=8001, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5433/user_service",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Max connections overflow")
    database_echo: bool = Field(default=False, description="Echo SQL queries (for debugging)")

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key (MUST be changed in production)",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days",
    )

    # Security
    password_bcrypt_rounds: int = Field(
        default=12,
        description="Bcrypt rounds for password hashing (higher = more secure but slower)",
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_allow_methods: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    cors_allow_headers: list[str] = Field(default=["*"], description="Allowed HTTP headers")

    # Redis (for sessions, cache)
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: str | None = Field(default=None, description="Redis password (if any)")

    # Health Check
    health_check_interval_seconds: int = Field(
        default=30,
        description="Health check interval",
    )

    @property
    def database_url_str(self) -> str:
        """Get database URL as string."""
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    """
    Получить настройки приложения (singleton pattern).

    Используем @lru_cache для создания единственного экземпляра настроек.
    Это гарантирует, что все части приложения используют одни и те же настройки.

    Returns:
        Settings: Настройки приложения
    """
    return Settings()


# Export для удобства импорта
settings = get_settings()
