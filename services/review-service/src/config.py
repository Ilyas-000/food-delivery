"""Review service configuration."""

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
    """Shared PostgreSQL settings."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", **_BASE_ENV_CONFIG)

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"


class KafkaSettings(BaseSettings):
    """Shared Kafka settings."""

    model_config = SettingsConfigDict(env_prefix="KAFKA_", **_BASE_ENV_CONFIG)

    bootstrap_servers: str = "localhost:9093"


class Settings(BaseSettings):
    """Review service settings."""

    model_config = SettingsConfigDict(env_prefix="REVIEW_SERVICE_", **_BASE_ENV_CONFIG)

    service_name: str = "review-service"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8008
    api_prefix: str = "/api/v1"

    db_name: str = "review_service_db"
    db_user: str | None = None
    db_password: str | None = None
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    test_database_url: str | None = None

    order_service_url: str = "http://order-service:8003"
    delivery_service_url: str = "http://delivery-service:8005"
    upstream_timeout_seconds: float = 5.0

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    kafka_enabled: bool = False

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL URL from settings."""
        user = self.db_user or self.postgres.user
        password = self.db_password or self.postgres.password
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres.host}:{self.postgres.port}/{self.db_name}"
        )

    @cached_property
    def postgres(self) -> PostgresSettings:
        """Get shared PostgreSQL settings."""
        return PostgresSettings()

    @cached_property
    def kafka(self) -> KafkaSettings:
        """Get shared Kafka settings."""
        return KafkaSettings()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
