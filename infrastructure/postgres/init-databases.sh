#!/usr/bin/env bash

set -euo pipefail

echo "Creating service databases and users..."

# Create databases (cannot use DO block for CREATE DATABASE)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- User Service
    SELECT 'CREATE DATABASE ${USER_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${USER_SERVICE_DB_NAME}')\gexec

    -- User Service (tests)
    SELECT 'CREATE DATABASE ${USER_SERVICE_TEST_DB_NAME:-user_service_test_db}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${USER_SERVICE_TEST_DB_NAME:-user_service_test_db}')\gexec

    -- Restaurant Service
    SELECT 'CREATE DATABASE ${RESTAURANT_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${RESTAURANT_SERVICE_DB_NAME}')\gexec

    -- Restaurant Service (tests)
    SELECT 'CREATE DATABASE ${RESTAURANT_SERVICE_TEST_DB_NAME:-restaurant_service_test_db}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${RESTAURANT_SERVICE_TEST_DB_NAME:-restaurant_service_test_db}')\gexec

    -- Order Service
    SELECT 'CREATE DATABASE ${ORDER_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${ORDER_SERVICE_DB_NAME}')\gexec

    -- Order Service (tests)
    SELECT 'CREATE DATABASE ${ORDER_SERVICE_TEST_DB_NAME:-order_service_test_db}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${ORDER_SERVICE_TEST_DB_NAME:-order_service_test_db}')\gexec

    -- Payment Service
    SELECT 'CREATE DATABASE ${PAYMENT_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${PAYMENT_SERVICE_DB_NAME}')\gexec

    -- Delivery Service
    SELECT 'CREATE DATABASE ${DELIVERY_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DELIVERY_SERVICE_DB_NAME}')\gexec

    -- Notification Service
    SELECT 'CREATE DATABASE ${NOTIFICATION_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${NOTIFICATION_SERVICE_DB_NAME}')\gexec

    -- Review Service
    SELECT 'CREATE DATABASE ${REVIEW_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${REVIEW_SERVICE_DB_NAME}')\gexec

    -- Review Service (tests)
    SELECT 'CREATE DATABASE ${REVIEW_SERVICE_TEST_DB_NAME:-review_service_test_db}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${REVIEW_SERVICE_TEST_DB_NAME:-review_service_test_db}')\gexec
EOSQL

echo "Databases created successfully."

create_role_and_grants() {
  local db_name="$1"
  local db_user="$2"
  local db_password="$3"

  if [ -z "${db_user}" ]; then
    return
  fi

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${db_user}') THEN
        CREATE ROLE "${db_user}" WITH LOGIN PASSWORD '${db_password}';
        RAISE NOTICE 'Created role: ${db_user}';
    END IF;
END
\$\$;

GRANT ALL PRIVILEGES ON DATABASE "${db_name}" TO "${POSTGRES_USER}";
EOSQL

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${db_name}" <<-EOSQL
GRANT ALL PRIVILEGES ON DATABASE "${db_name}" TO "${db_user}";
GRANT USAGE, CREATE ON SCHEMA public TO "${db_user}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${db_user}";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "${db_user}";
EOSQL
}

services=(
  "USER_SERVICE"
  "RESTAURANT_SERVICE"
  "ORDER_SERVICE"
  "PAYMENT_SERVICE"
  "DELIVERY_SERVICE"
  "NOTIFICATION_SERVICE"
  "REVIEW_SERVICE"
)

for service in "${services[@]}"; do
  db_name_var="${service}_DB_NAME"
  db_user_var="${service}_DB_USER"
  db_password_var="${service}_DB_PASSWORD"

  db_name="${!db_name_var:-}"
  db_user="${!db_user_var:-}"
  db_password="${!db_password_var:-}"

  if [ -n "${db_name}" ]; then
    create_role_and_grants "${db_name}" "${db_user}" "${db_password}"
  fi
done

# Integration tests should use isolated databases to avoid mutating runtime data.
create_role_and_grants \
  "${USER_SERVICE_TEST_DB_NAME:-user_service_test_db}" \
  "${USER_SERVICE_DB_USER:-}" \
  "${USER_SERVICE_DB_PASSWORD:-}"
create_role_and_grants \
  "${RESTAURANT_SERVICE_TEST_DB_NAME:-restaurant_service_test_db}" \
  "${RESTAURANT_SERVICE_DB_USER:-}" \
  "${RESTAURANT_SERVICE_DB_PASSWORD:-}"
create_role_and_grants \
  "${ORDER_SERVICE_TEST_DB_NAME:-order_service_test_db}" \
  "${ORDER_SERVICE_DB_USER:-}" \
  "${ORDER_SERVICE_DB_PASSWORD:-}"
create_role_and_grants \
  "${REVIEW_SERVICE_TEST_DB_NAME:-review_service_test_db}" \
  "${REVIEW_SERVICE_DB_USER:-}" \
  "${REVIEW_SERVICE_DB_PASSWORD:-}"

echo "Database initialization complete."
