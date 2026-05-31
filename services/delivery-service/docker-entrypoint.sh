#!/usr/bin/env bash

set -euo pipefail

echo "=== Delivery Service Entrypoint ==="

echo "Waiting for PostgreSQL..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready"

echo "Running database migrations..."
cd /app/services/delivery-service
alembic upgrade head
echo "✓ Migrations completed"

echo "Starting Delivery Service on ${DELIVERY_SERVICE_API_HOST:-0.0.0.0}:${DELIVERY_SERVICE_API_PORT:-8005}"
exec uvicorn src.main:app \
  --host "${DELIVERY_SERVICE_API_HOST:-0.0.0.0}" \
  --port "${DELIVERY_SERVICE_API_PORT:-8005}"
