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
