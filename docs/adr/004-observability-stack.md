# ADR-004: Monitoring and Observability Stack

**Status**: Accepted
**Date**: 2026-04-07
**Authors**: Food Delivery Team
**Deciders**: Engineering Team

## Context

By the end of Phase 9 the platform had working service contracts and end-to-end tests,
but no unified observability story. We needed:
- technical metrics for HTTP traffic and gateway resilience;
- business counters for core delivery flow milestones;
- centralized logs across compose-managed services;
- request correlation across gateway and downstream services;
- dashboards and alerts without introducing heavy operational complexity.

## Decision

We will use a compose-friendly observability stack built around:
- Prometheus for metrics scraping and alert evaluation;
- Alertmanager for alert routing;
- Grafana for dashboards and exploration;
- Loki + Promtail for centralized container logs;
- shared request/correlation id middleware for lightweight cross-service tracing.

Application-level instrumentation will stay in `shared` when it is generic
(HTTP metrics, request context propagation) and remain service-local when it is
domain- or service-specific (gateway resilience metrics, business counters).

## Consequences

### Positive Consequences

- Every service exposes `/metrics` consistently.
- Gateway failures and throttling are observable without log parsing.
- Logs become queryable in one place through Grafana/Loki.
- Request paths can be correlated across services using shared headers.
- The stack stays runnable in local Docker Compose without a separate platform team.

### Negative Consequences

- Correlation tracing is lighter-weight than full OpenTelemetry spans.
- Promtail/Loki adds more moving parts to the local compose environment.
- Alert rules are intentionally simple and may need tuning as traffic patterns evolve.

### Risks

- Promtail log discovery may need host-specific adjustments on some Docker setups.
- Correlation-id based tracing gives less detail than span-based tracing; if that becomes limiting, migrate to OpenTelemetry later without replacing the current metrics/logging baseline.

## Alternatives Considered

### Alternative 1: Full OpenTelemetry + Tempo/Jaeger immediately

**Pros**:
- richer distributed tracing;
- standard span model.

**Cons**:
- more dependencies and runtime complexity;
- higher rollout cost across every service.

**Why rejected**: Too much operational weight for the current educational/local-first stage.

### Alternative 2: Metrics only, no centralized logs

**Pros**:
- smallest implementation footprint;
- fewer infra services.

**Cons**:
- harder debugging for cross-service failures;
- no single place to inspect service logs.

**Why rejected**: Phase 10 explicitly requires logs/observability beyond metrics alone.

## Implementation Notes

- Shared helpers live in `shared/src/shared/observability`.
- Prometheus scrape rules and alerts live in `infrastructure/docker/prometheus`.
- Grafana datasources and dashboards are provisioned from `infrastructure/docker/grafana`.
- Loki/Promtail configuration lives in `infrastructure/docker/loki` and `infrastructure/docker/promtail`.

## References

- `PROGRESS.md`
- `docs/ENGINEERING_CONVENTIONS.md`
- `infrastructure/docker-compose.yml`
