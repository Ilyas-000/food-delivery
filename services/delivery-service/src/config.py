"""Delivery Service settings."""

from functools import cached_property, lru_cache
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    """Shared PostgreSQL settings."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="POSTGRES_",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"


class KafkaSettings(BaseSettings):
    """Shared Kafka settings."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="KAFKA_",
        case_sensitive=False,
        extra="ignore",
    )

    bootstrap_servers: str = "localhost:9093"


class Settings(BaseSettings):
    """Runtime configuration for Delivery Service."""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_prefix="DELIVERY_SERVICE_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "delivery-service"
    environment: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"  # nosec B104
    api_port: int = 8005
    api_prefix: str = "/api/v1"
    metrics_enabled: bool = True
    metrics_path: str = "/metrics"

    realtime_backend: str = "memory"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 2
    redis_password: str | None = None
    redis_channel_prefix: str = "delivery"
    kafka_enabled: bool = False

    db_name: str = "delivery_service_db"
    db_user: str | None = None
    db_password: str | None = None
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    test_database_url: str | None = None

    mock_courier_ids: str = (
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1,"
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2,"
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"
    )

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

    @cached_property
    def courier_ids(self) -> tuple[UUID, ...]:
        """Parse configured courier identities for local assignment flow."""
        return tuple(
            UUID(raw_id.strip()) for raw_id in self.mock_courier_ids.split(",") if raw_id.strip()
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
