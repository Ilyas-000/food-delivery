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

# Run database migrations
echo "Running database migrations..."
cd /app/services/user-service
alembic upgrade head
echo "✓ Migrations completed"

# Start the application
log_level="${USER_SERVICE_LOG_LEVEL:-info}"
log_level="${log_level,,}"

echo "Starting User Service on ${USER_SERVICE_API_HOST:-0.0.0.0}:${USER_SERVICE_API_PORT:-8001}"
cd /app/services/user-service
exec uvicorn src.main:app \
  --host "${USER_SERVICE_API_HOST:-0.0.0.0}" \
  --port "${USER_SERVICE_API_PORT:-8001}" \
  --log-level "${log_level}"
