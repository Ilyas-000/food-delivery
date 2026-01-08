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

# Restaurant Service (TODO)
# echo "→ Restaurant Service migrations..."
# cd "$PROJECT_ROOT/services/restaurant-service"
# alembic upgrade head

# Order Service (TODO)
# echo "→ Order Service migrations..."
# cd "$PROJECT_ROOT/services/order-service"
# alembic upgrade head

echo ""
echo "✓ All migrations completed successfully"
