#!/usr/bin/env bash

set -euo pipefail

echo "=== Restaurant Service Entrypoint ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready"

# Run database migrations
echo "Running database migrations..."
cd /app/services/restaurant-service
alembic upgrade head
echo "✓ Migrations completed"

# Start the application
cd /app/services/restaurant-service
log_level="$(python - <<'PY'
from src.config import settings

print(settings.log_level.lower())
PY
)"

echo "Starting Restaurant Service on ${RESTAURANT_SERVICE_API_HOST:-0.0.0.0}:${RESTAURANT_SERVICE_API_PORT:-8002}"
exec uvicorn src.main:app \
  --host "${RESTAURANT_SERVICE_API_HOST:-0.0.0.0}" \
  --port "${RESTAURANT_SERVICE_API_PORT:-8002}" \
  --log-level "${log_level}"
