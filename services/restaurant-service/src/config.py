"""
Restaurant Service Configuration.

Loads settings from environment variables using pydantic-settings.
"""

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


class PostgresSettings(BaseSettings):
    """PostgreSQL settings shared across services."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", **_BASE_ENV_CONFIG)

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"


class Settings(BaseSettings):
    """Restaurant Service Settings."""

    model_config = SettingsConfigDict(
        env_prefix="RESTAURANT_SERVICE_",
        **_BASE_ENV_CONFIG,
    )

    # Service
    service_name: str = "restaurant-service"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8002
    api_prefix: str = "/api/v1"

    # Database
    db_name: str = "restaurant_service_db"  # Uses prefix: RESTAURANT_SERVICE_DB_NAME
    db_user: str | None = None  # Uses prefix: RESTAURANT_SERVICE_DB_USER
    db_password: str | None = None  # Uses prefix: RESTAURANT_SERVICE_DB_PASSWORD

    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    test_database_url: str | None = None

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL URL from separate variables."""
        user = self.db_user or self.postgres.user
        password = self.db_password or self.postgres.password
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres.host}:{self.postgres.port}/{self.db_name}"
        )

    @cached_property
    def postgres(self) -> PostgresSettings:
        """Lazy-load shared PostgreSQL settings."""
        return PostgresSettings()

    # Redis (for caching popular restaurants and menus)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 2  # Separate DB from User Service (0) and API Gateway (1)
    redis_password: str | None = None

    # Cache TTL (seconds)
    cache_restaurant_ttl: int = 300  # 5 minutes
    cache_menu_ttl: int = 120  # 2 minutes
    cache_popular_restaurants_ttl: int = 300  # 5 minutes

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Search
    search_results_per_page: int = 20
    search_max_page_size: int = 100

    # Authorization
    trust_gateway_headers: bool = True  # Trust X-User-ID from API Gateway


@lru_cache
def get_settings() -> Settings:
    """Get settings singleton."""
    return Settings()


settings = get_settings()
