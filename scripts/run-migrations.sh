#!/usr/bin/env bash

set -euo pipefail

echo "Running database migrations for all services..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# User Service
echo "→ User Service migrations..."
cd "$PROJECT_ROOT/services/user-service"
if [ -d "alembic" ]; then
    alembic upgrade head
    echo "✓ User Service migrations completed"
else
    echo "⚠ User Service: No Alembic configuration found"
fi

# Restaurant Service
echo "→ Restaurant Service migrations..."
cd "$PROJECT_ROOT/services/restaurant-service"
if [ -d "alembic" ]; then
    alembic upgrade head
    echo "✓ Restaurant Service migrations completed"
else
    echo "⚠ Restaurant Service: No Alembic configuration found"
fi

# Order Service
echo "→ Order Service migrations..."
cd "$PROJECT_ROOT/services/order-service"
if [ -d "alembic" ]; then
    alembic upgrade head
    echo "✓ Order Service migrations completed"
else
    echo "⚠ Order Service: No Alembic configuration found"
fi

echo ""
echo "✓ All migrations completed successfully"
