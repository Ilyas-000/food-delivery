#!/usr/bin/env bash

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "Checking service health..."
echo ""

# Check PostgreSQL
if docker exec food-delivery-postgres pg_isready -U postgres &> /dev/null; then
  echo -e "${GREEN}✓${NC} PostgreSQL is healthy"
else
  echo -e "${RED}✗${NC} PostgreSQL is down"
fi

# Check Redis
if docker exec food-delivery-redis redis-cli ping &> /dev/null; then
  echo -e "${GREEN}✓${NC} Redis is healthy"
else
  echo -e "${RED}✗${NC} Redis is down"
fi

# Check Kafka
if docker exec food-delivery-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
  echo -e "${GREEN}✓${NC} Kafka is healthy"
else
  echo -e "${RED}✗${NC} Kafka is down"
fi

check_container_health() {
  local name="$1"
  local label="$2"

  if ! docker ps -a --format '{{.Names}}' | grep -q "^${name}$"; then
    echo -e "${YELLOW}!${NC} ${label} container is not running"
    return
  fi

  local status
  status="$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{end}}' "${name}" 2>/dev/null)"
  if [ -z "${status}" ]; then
    local runtime_status
    runtime_status="$(docker inspect --format='{{.State.Status}}' "${name}" 2>/dev/null || echo "unknown")"
    if [ "${runtime_status}" = "running" ]; then
      echo -e "${GREEN}✓${NC} ${label} is running (no healthcheck)"
    else
      echo -e "${RED}✗${NC} ${label} is ${runtime_status}"
    fi
    return
  fi
  if [ "${status}" = "healthy" ]; then
    echo -e "${GREEN}✓${NC} ${label} is healthy"
  elif [ "${status}" = "starting" ]; then
    echo -e "${YELLOW}!${NC} ${label} is starting"
  elif [ "${status}" = "unhealthy" ]; then
    echo -e "${RED}✗${NC} ${label} is unhealthy"
  else
    echo -e "${YELLOW}!${NC} ${label} health is unknown"
  fi
}

# Check Zookeeper, Kafka UI, and PgAdmin (if running)
check_container_health "food-delivery-zookeeper" "Zookeeper"
check_container_health "food-delivery-kafka-ui" "Kafka UI"
check_container_health "food-delivery-pgadmin" "PgAdmin"

# Check User Service and API Gateway (if running)
check_container_health "food-delivery-user-service" "User Service"
check_container_health "food-delivery-restaurant-service" "Restaurant Service"
check_container_health "food-delivery-order-service" "Order Service"
check_container_health "food-delivery-payment-service" "Payment Service"
check_container_health "food-delivery-delivery-service" "Delivery Service"
check_container_health "food-delivery-notification-service" "Notification Service"
check_container_health "food-delivery-analytics-service" "Analytics Service"
check_container_health "food-delivery-api-gateway" "API Gateway"

if docker ps -a --format '{{.Names}}' | grep -q '^food-delivery-clickhouse$'; then
  if docker exec food-delivery-clickhouse clickhouse-client --query "SELECT 1" &> /dev/null; then
    echo -e "${GREEN}✓${NC} ClickHouse is healthy"
  else
    echo -e "${RED}✗${NC} ClickHouse is down"
  fi
else
  echo -e "${YELLOW}!${NC} ClickHouse is not configured in this environment"
fi

echo ""
echo "Health check complete!"
