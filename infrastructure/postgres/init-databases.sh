#!/usr/bin/env bash

set -euo pipefail

echo "Creating service databases (if missing)..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${USER_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${USER_SERVICE_DB_NAME}";
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${RESTAURANT_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${RESTAURANT_SERVICE_DB_NAME}";
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${ORDER_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${ORDER_SERVICE_DB_NAME}";
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${PAYMENT_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${PAYMENT_SERVICE_DB_NAME}";
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DELIVERY_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${DELIVERY_SERVICE_DB_NAME}";
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${NOTIFICATION_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${NOTIFICATION_SERVICE_DB_NAME}";
    END IF;
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '${REVIEW_SERVICE_DB_NAME}') THEN
        CREATE DATABASE "${REVIEW_SERVICE_DB_NAME}";
    END IF;
END
\$\$;
EOSQL

echo "Database initialization complete."
