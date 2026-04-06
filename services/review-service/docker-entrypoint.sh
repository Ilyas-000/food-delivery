#!/usr/bin/env bash

set -euo pipefail

echo "=== Review Service Entrypoint ==="

echo "Waiting for PostgreSQL..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready"

echo "Running database migrations..."
cd /app/services/review-service
alembic upgrade head
echo "✓ Migrations completed"

cd /app/services/review-service
log_level="$(python - <<'PY'
from src.config import settings

print(settings.log_level.lower())
PY
)"

echo "Starting Review Service on ${REVIEW_SERVICE_API_HOST:-0.0.0.0}:${REVIEW_SERVICE_API_PORT:-8008}"
exec uvicorn src.main:app \
  --host "${REVIEW_SERVICE_API_HOST:-0.0.0.0}" \
  --port "${REVIEW_SERVICE_API_PORT:-8008}" \
  --log-level "${log_level}"
