#!/usr/bin/env bash

set -euo pipefail

# Configuration
KAFKA_CONTAINER=${KAFKA_CONTAINER:-food-delivery-kafka}
BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-localhost:9092}
PARTITIONS=${PARTITIONS:-3}  # 3 partitions for better parallelism
REPLICATION_FACTOR=${REPLICATION_FACTOR:-1}  # 1 for local dev

# Execution mode:
#   docker (default) - run the Kafka CLI on the host via `docker exec` into the broker container
#   direct           - run the Kafka CLI directly (used by the in-cluster kafka-init compose job)
KAFKA_EXEC_MODE=${KAFKA_EXEC_MODE:-docker}

kafka_cli() {
  if [ "$KAFKA_EXEC_MODE" = "direct" ]; then
    "$@"
  else
    docker exec "$KAFKA_CONTAINER" "$@"
  fi
}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Topic definitions
# Format: "topic_name:partitions:retention_ms"
# retention_ms: -1 = infinite, 86400000 = 1 day, 604800000 = 7 days
TOPICS=(
  # Order Service Events
  "order-service.order.created:3:604800000"
  "order-service.order.confirmed:3:604800000"
  "order-service.order.cancelled:3:604800000"
  "order-service.order.delivered:3:604800000"

  # Payment Service Events
  "payment-service.payment.reserved:3:604800000"
  "payment-service.payment.completed:3:604800000"
  "payment-service.payment.failed:3:604800000"
  "payment-service.payment.refunded:3:604800000"

  # Delivery Service Events
  "delivery-service.delivery.assigned:3:604800000"
  "delivery-service.delivery.picked_up:3:604800000"
  "delivery-service.delivery.in_transit:3:604800000"
  "delivery-service.delivery.completed:3:604800000"
  "delivery-service.delivery.location_updated:3:86400000"  # 1 day retention for location updates

  # User Service Events
  "user-service.user.registered:3:604800000"
  "user-service.user.updated:3:604800000"

  # Restaurant Service Events
  "restaurant-service.restaurant.created:3:604800000"
  "restaurant-service.restaurant.updated:3:604800000"
  "restaurant-service.restaurant.deactivated:3:604800000"
  "restaurant-service.menu_item.created:3:604800000"
  "restaurant-service.menu_item.updated:3:604800000"
  "restaurant-service.menu_item.availability_changed:3:604800000"
  "restaurant-service.menu_item.deleted:3:604800000"

  # Notification Service Events
  "notification-service.notification.email_sent:3:86400000"
  "notification-service.notification.push_sent:3:86400000"

  # Review Service Events
  "review-service.review.created:3:604800000"

  # Saga Coordination (for Order Saga)
  "order-service.saga.step_completed:3:604800000"
  "order-service.saga.step_failed:3:604800000"
)

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Kafka Topics Creation                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Container:${NC} $KAFKA_CONTAINER"
echo -e "${BLUE}Bootstrap:${NC} $BOOTSTRAP_SERVER"
echo -e "${BLUE}Default Partitions:${NC} $PARTITIONS"
echo -e "${BLUE}Replication Factor:${NC} $REPLICATION_FACTOR"
echo ""

# Wait for Kafka to be ready
echo -e "${YELLOW}Waiting for Kafka to be ready...${NC}"
MAX_RETRIES=30
RETRY=0
while ! kafka_cli kafka-broker-api-versions --bootstrap-server "$BOOTSTRAP_SERVER" &> /dev/null; do
  RETRY=$((RETRY + 1))
  if [ $RETRY -gt $MAX_RETRIES ]; then
    echo -e "${YELLOW}Kafka is not ready after ${MAX_RETRIES} attempts. Exiting.${NC}"
    exit 1
  fi
  echo -e "${YELLOW}Attempt $RETRY/$MAX_RETRIES...${NC}"
  sleep 2
done
echo -e "${GREEN}✓ Kafka is ready${NC}"
echo ""

# Create topics
echo -e "${BLUE}Creating topics...${NC}"
for topic_config in "${TOPICS[@]}"; do
  IFS=':' read -r topic partitions retention <<< "$topic_config"

  # Use default partitions if not specified
  partitions=${partitions:-$PARTITIONS}
  retention=${retention:-604800000}  # Default 7 days

  echo -e "${BLUE}→ ${topic}${NC} (partitions: $partitions, retention: $retention ms)"

  kafka_cli kafka-topics \
    --bootstrap-server "$BOOTSTRAP_SERVER" \
    --create \
    --if-not-exists \
    --topic "$topic" \
    --partitions "$partitions" \
    --replication-factor "$REPLICATION_FACTOR" \
    --config retention.ms="$retention" \
    2>&1 | grep -v "already exists" || true
done

echo ""
echo -e "${GREEN}✓ All topics created${NC}"
echo ""

# List all topics
echo -e "${BLUE}Listing all topics:${NC}"
kafka_cli kafka-topics \
  --bootstrap-server "$BOOTSTRAP_SERVER" \
  --list

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Topics ready! 🎉                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
