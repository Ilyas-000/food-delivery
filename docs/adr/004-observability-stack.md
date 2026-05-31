# ADR-004: Observability Stack

**Status**: Accepted
**Date**: 2026-04-07
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

The platform has multiple FastAPI services behind a gateway, several infrastructure dependencies, Kafka consumers and background retry loops. Debugging requires more than individual container logs.

The observability baseline must provide:
- HTTP metrics for gateway and services;
- service-specific counters where they are operationally useful;
- centralized container logs;
- request correlation across gateway and downstream services;
- a local Docker Compose profile that does not require a separate platform stack.

## Decision

The repository includes a Docker Compose monitoring profile with:
- Prometheus for metrics scraping and alert rule evaluation;
- Alertmanager for alert routing;
- Grafana for dashboards and log exploration;
- Loki and Promtail for container logs;
- shared request/correlation id middleware for lightweight cross-service tracing.

Common HTTP instrumentation lives in `shared/src/shared/observability`. Service-specific metrics stay in the service that owns the behavior.

## Consequences

### Positive

- Every service can expose `/metrics` consistently.
- Gateway throttling and circuit breaker behavior can be observed without reading raw logs.
- Container logs are queryable from one place.
- `X-Request-ID` and `X-Correlation-ID` make request paths traceable through gateway and downstream calls.
- The stack remains runnable from Docker Compose.

### Negative

- Correlation-id tracing is less detailed than span-based tracing.
- Loki and Promtail add services to local runtime.
- Alert thresholds need tuning with real traffic data.

### Risks

- Docker log discovery can differ between host setups.
- Missing OpenTelemetry spans limits latency breakdown inside multi-hop flows.

## Alternatives Considered

### OpenTelemetry with Tempo or Jaeger immediately

**Pros**:
- Standard distributed tracing model.
- Detailed span timing across service boundaries.

**Cons**:
- More moving parts and instrumentation work.
- Harder local setup.

**Why rejected**: metrics, logs and request correlation cover the current debugging needs with less runtime complexity.

### Metrics only

**Pros**:
- Smallest infrastructure footprint.
- Easier setup.

**Cons**:
- Multi-service failures are harder to diagnose without centralized logs.
- Log search stays fragmented across containers.

**Why rejected**: centralized logs are necessary for gateway/downstream and consumer debugging.

## Implementation Notes

- Prometheus config: `infrastructure/docker/prometheus/prometheus.yml`
- Alert rules: `infrastructure/docker/prometheus/alerts`
- Grafana provisioning: `infrastructure/docker/grafana`
- Loki config: `infrastructure/docker/loki/loki.yml`
- Promtail config: `infrastructure/docker/promtail/promtail.yml`
- Shared instrumentation: `shared/src/shared/observability`

## References

- [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md)
- [docs/ENGINEERING_CONVENTIONS.md](../ENGINEERING_CONVENTIONS.md)
