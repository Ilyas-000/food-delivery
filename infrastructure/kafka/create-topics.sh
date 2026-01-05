#!/usr/bin/env bash

set -euo pipefail

KAFKA_CONTAINER=${KAFKA_CONTAINER:-food-delivery-kafka}
BOOTSTRAP_SERVER=${BOOTSTRAP_SERVER:-localhost:9092}
PARTITIONS=${PARTITIONS:-1}
REPLICATION_FACTOR=${REPLICATION_FACTOR:-1}

TOPICS=(
  "order.order.created"
  "order.order.confirmed"
  "order.order.cancelled"
  "payment.payment.reserved"
  "payment.payment.failed"
  "delivery.delivery.assigned"
  "delivery.delivery.completed"
  "notification.notification.sent"
)

echo "Creating Kafka topics in container: ${KAFKA_CONTAINER}"

for topic in "${TOPICS[@]}"; do
  docker exec "$KAFKA_CONTAINER" kafka-topics \
    --bootstrap-server "$BOOTSTRAP_SERVER" \
    --create \
    --if-not-exists \
    --topic "$topic" \
    --partitions "$PARTITIONS" \
    --replication-factor "$REPLICATION_FACTOR"
done

echo "Kafka topics ready."
