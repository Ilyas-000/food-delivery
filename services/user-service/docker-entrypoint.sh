#!/usr/bin/env bash

set -euo pipefail

echo "=== User Service Entrypoint ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready"

# Wait for Redis to be ready
echo "Waiting for Redis..."
until python - <<'PY'
import asyncio
import os

import redis.asyncio as redis


async def main() -> None:
    host = os.getenv("USER_SERVICE_REDIS_HOST") or os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("USER_SERVICE_REDIS_PORT") or os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("USER_SERVICE_REDIS_DB") or os.getenv("REDIS_DB", "0"))
    password = os.getenv("USER_SERVICE_REDIS_PASSWORD") or os.getenv("REDIS_PASSWORD")
    client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
    try:
        await client.ping()
    finally:
        await client.close()


asyncio.run(main())
PY
do
  echo "Redis is unavailable - sleeping"
  sleep 2
done

echo "✓ Redis is ready"

# Run database migrations
echo "Running database migrations..."
cd /app/services/user-service
alembic upgrade head
echo "✓ Migrations completed"

# Start the application
cd /app/services/user-service
log_level="$(python - <<'PY'
from src.config import settings

print(settings.log_level)
PY
)"

echo "Starting User Service on ${USER_SERVICE_API_HOST:-0.0.0.0}:${USER_SERVICE_API_PORT:-8001}"
exec uvicorn src.main:app \
  --host "${USER_SERVICE_API_HOST:-0.0.0.0}" \
  --port "${USER_SERVICE_API_PORT:-8001}" \
  --log-level "${log_level}"
