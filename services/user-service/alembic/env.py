"""
Alembic environment configuration for User Service.

This module configures Alembic to work with our SQLAlchemy models.

IMPORTANT:
- Imports Base from infrastructure/database/base.py
- Imports ALL models so Alembic can detect them
- Reads database URL from settings (not from alembic.ini)
- Supports async SQLAlchemy
"""

import asyncio
from logging.config import fileConfig
from pathlib import Path
import sys

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context  # type: ignore[attr-defined]

# Add src to Python path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings  # noqa: E402

# Import Base (contains metadata)
from src.infrastructure.database.base import Base  # noqa: E402

# CRITICAL: Import all models here so Alembic can detect them!
# If you don't import models, Alembic won't generate migrations for them
from src.infrastructure.database.models.user_model import UserModel  # noqa: F401,E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with our settings
# This allows us to use environment variables instead of hardcoding in alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata to Base.metadata
# This tells Alembic about our models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare types to detect column type changes
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with given connection.

    Args:
        connection: SQLAlchemy connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Compare types to detect column type changes
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    This is for async SQLAlchemy support.
    """
    # Create async engine
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Run migrations in sync context (Alembic doesn't support async yet)
        await connection.run_sync(do_run_migrations)

    # Dispose engine
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Wrapper for async migration runner.
    """
    asyncio.run(run_async_migrations())


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
