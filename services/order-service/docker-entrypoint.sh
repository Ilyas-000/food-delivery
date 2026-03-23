#!/usr/bin/env bash

set -euo pipefail

echo "=== Order Service Entrypoint ==="

cd /app/services/order-service

if [ "${ORDER_SERVICE_REPOSITORY_BACKEND:-memory}" = "postgres" ]; then
  echo "Waiting for PostgreSQL..."
  until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
  done
  echo "✓ PostgreSQL is ready"

  echo "Running database migrations..."
  alembic upgrade head
  echo "✓ Migrations completed"
fi

log_level="$(python - <<'PY'
from src.config import settings

print(settings.log_level.lower())
PY
)"

echo "Starting Order Service on ${ORDER_SERVICE_API_HOST:-0.0.0.0}:${ORDER_SERVICE_API_PORT:-8003}"
exec uvicorn src.main:app \
  --host "${ORDER_SERVICE_API_HOST:-0.0.0.0}" \
  --port "${ORDER_SERVICE_API_PORT:-8003}" \
  --log-level "${log_level}"
