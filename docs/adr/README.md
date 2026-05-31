# Architecture Decision Records

Каталог содержит ADR проекта Food Delivery Platform. ADR фиксирует решение, контекст, последствия и отклонённые альтернативы. Документ не должен ссылаться на локальные агентские файлы, внутренние этапы разработки или неотслеживаемые артефакты.

## Статусы

- `Proposed` — решение предложено, но ещё не является обязательным правилом.
- `Accepted` — решение принято и применяется в проекте.
- `Deprecated` — решение больше не рекомендуется.
- `Superseded` — решение заменено другим ADR.

## Список ADR

| # | Файл | Решение | Статус | Дата |
|---:|---|---|---|---|
| 001 | [001-microservices-architecture-baseline.md](001-microservices-architecture-baseline.md) | Базовая микросервисная архитектура | Accepted | 2026-05-31 |
| 002 | [002-saga-orchestration-strategy.md](002-saga-orchestration-strategy.md) | Saga-оркестрация заказа | Accepted | 2026-05-31 |
| 003 | [003-restaurant-service-architecture.md](003-restaurant-service-architecture.md) | Архитектура Restaurant Service | Accepted | 2026-01-31 |
| 004 | [004-observability-stack.md](004-observability-stack.md) | Стек мониторинга и observability | Accepted | 2026-04-07 |
| 005 | [005-outbox-pattern-reliable-events.md](005-outbox-pattern-reliable-events.md) | Outbox pattern для Kafka-событий | Proposed | 2026-05-31 |
| 006 | [006-clean-architecture-conventions.md](006-clean-architecture-conventions.md) | Clean Architecture между сервисами | Accepted | 2026-05-31 |
| 007 | [007-websocket-redis-pubsub-delivery-tracking.md](007-websocket-redis-pubsub-delivery-tracking.md) | WebSocket + Redis Pub/Sub для delivery tracking | Accepted | 2026-05-31 |
| 008 | [008-postgresql-database-per-service.md](008-postgresql-database-per-service.md) | PostgreSQL database-per-service | Accepted | 2026-05-31 |

## Создание нового ADR

```bash
cp docs/adr/template.md docs/adr/XXX-short-title.md
```

Новый номер должен быть следующим свободным числом. В тексте фиксируются факты и trade-offs, без маркетинговых формулировок и ссылок на локальные рабочие заметки.
