#!/usr/bin/env bash

set -euo pipefail

echo "Creating service databases and users..."

# Create databases (cannot use DO block for CREATE DATABASE)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- User Service
    SELECT 'CREATE DATABASE ${USER_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${USER_SERVICE_DB_NAME}')\gexec

    -- Restaurant Service
    SELECT 'CREATE DATABASE ${RESTAURANT_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${RESTAURANT_SERVICE_DB_NAME}')\gexec

    -- Order Service
    SELECT 'CREATE DATABASE ${ORDER_SERVICE_DB_NAME}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${ORDER_SERVICE_DB_NAME}')\gexec

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
EOSQL

echo "Databases created successfully."

# Create users and grant privileges (can use DO block for these)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
DO \$\$
BEGIN
    -- User Service user (if configured)
    IF '${USER_SERVICE_DB_USER:-}' != '' THEN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${USER_SERVICE_DB_USER}') THEN
            CREATE ROLE "${USER_SERVICE_DB_USER}" WITH LOGIN PASSWORD '${USER_SERVICE_DB_PASSWORD}';
            RAISE NOTICE 'Created role: ${USER_SERVICE_DB_USER}';
        END IF;
    END IF;
END
\$\$;

-- Grant privileges (must be outside DO block)
GRANT ALL PRIVILEGES ON DATABASE "${USER_SERVICE_DB_NAME}" TO "${POSTGRES_USER}";
EOSQL

if [ -n "${USER_SERVICE_DB_USER:-}" ]; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${USER_SERVICE_DB_NAME}" <<-EOSQL
  GRANT ALL PRIVILEGES ON DATABASE "${USER_SERVICE_DB_NAME}" TO "${USER_SERVICE_DB_USER}";
  GRANT USAGE, CREATE ON SCHEMA public TO "${USER_SERVICE_DB_USER}";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${USER_SERVICE_DB_USER}";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "${USER_SERVICE_DB_USER}";
EOSQL
fi

echo "Database initialization complete."
