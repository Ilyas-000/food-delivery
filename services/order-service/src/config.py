"""Order Service settings."""

from functools import cached_property, lru_cache
from typing import cast

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_ENV_CONFIG = cast(
    SettingsConfigDict,
    {
        "env_file": "../../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    },
)


class Settings(BaseSettings):
    """Runtime configuration for Order Service."""

    model_config = SettingsConfigDict(env_prefix="ORDER_SERVICE_", **_BASE_ENV_CONFIG)

    service_name: str = "order-service"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8003
    api_prefix: str = "/api/v1"

    repository_backend: str = "memory"
    saga_backend: str = "mock"
    saga_step_timeout_seconds: float = 5.0

    restaurant_service_url: str = "http://restaurant-service:8002"
    payment_service_url: str = "http://payment-service:8004"
    delivery_service_url: str = "http://delivery-service:8005"

    db_name: str = "order_service_db"
    db_user: str | None = None
    db_password: str | None = None
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    test_database_url: str | None = None

    @cached_property
    def postgres(self) -> "PostgresSettings":
        """Get shared PostgreSQL settings."""
        return PostgresSettings()

    @property
    def database_url(self) -> str:
        """Build async SQLAlchemy connection string."""
        user = self.db_user or self.postgres.user
        password = self.db_password or self.postgres.password
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres.host}:{self.postgres.port}/{self.db_name}"
        )


class PostgresSettings(BaseSettings):
    """Shared PostgreSQL settings."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", **_BASE_ENV_CONFIG)

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
