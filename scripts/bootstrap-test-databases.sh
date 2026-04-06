#!/usr/bin/env bash

set -euo pipefail

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-food-delivery-postgres}"

if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
  echo "Postgres container '${POSTGRES_CONTAINER}' is not running"
  exit 1
fi

docker exec "${POSTGRES_CONTAINER}" bash -lc '
set -euo pipefail

ensure_database() {
  local db_name="$1"

  if [ -z "${db_name}" ]; then
    return
  fi

  if ! psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname = '\''${db_name}'\''" | grep -q 1; then
    psql -q -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -c \
      "CREATE DATABASE \"${db_name}\"" >/dev/null
  fi
}

ensure_role_and_grants() {
  local db_name="$1"
  local db_user="$2"
  local db_password="$3"

  if [ -z "${db_name}" ] || [ -z "${db_user}" ]; then
    return
  fi

  if ! psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname = '\''${db_user}'\''" | grep -q 1; then
    psql -q -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -c \
      "CREATE ROLE \"${db_user}\" WITH LOGIN PASSWORD '\''${db_password}'\''" >/dev/null
  fi

  psql -q -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres -c \
    "GRANT ALL PRIVILEGES ON DATABASE \"${db_name}\" TO \"${db_user}\"" >/dev/null
  psql -q -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "${db_name}" -c \
    "GRANT USAGE, CREATE ON SCHEMA public TO \"${db_user}\"" >/dev/null
  psql -q -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "${db_name}" -c \
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO \"${db_user}\"" >/dev/null
  psql -q -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "${db_name}" -c \
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO \"${db_user}\"" >/dev/null
}

bootstrap_service_db() {
  local db_name="$1"
  local db_user="$2"
  local db_password="$3"

  ensure_database "$db_name"
  ensure_role_and_grants "$db_name" "$db_user" "$db_password"
}

bootstrap_service_db "${USER_SERVICE_TEST_DB_NAME:-user_service_test_db}" "${USER_SERVICE_DB_USER:-}" "${USER_SERVICE_DB_PASSWORD:-}"
bootstrap_service_db "${RESTAURANT_SERVICE_TEST_DB_NAME:-restaurant_service_test_db}" "${RESTAURANT_SERVICE_DB_USER:-}" "${RESTAURANT_SERVICE_DB_PASSWORD:-}"
bootstrap_service_db "${ORDER_SERVICE_TEST_DB_NAME:-order_service_test_db}" "${ORDER_SERVICE_DB_USER:-}" "${ORDER_SERVICE_DB_PASSWORD:-}"
bootstrap_service_db "${REVIEW_SERVICE_TEST_DB_NAME:-review_service_test_db}" "${REVIEW_SERVICE_DB_USER:-}" "${REVIEW_SERVICE_DB_PASSWORD:-}"
'
