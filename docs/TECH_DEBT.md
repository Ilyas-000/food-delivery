# Technical Debt

## Backlog

- Naming consistency: simplify and clarify naming (DTO/use_case, module names, route names).
- API responses metadata: large inline `responses` blocks in routes should be simplified or moved.
- Swagger: дублируются разделы auth/authentication в User Service (`/docs`).
- Tests DB: разногласия по стратегии поднятия тестовой БД (auto-create/drop vs ручной жизненный цикл).
- Redis close: mypy не знает про `aclose()` в redis.asyncio, сейчас есть временный type workaround.

---

## API Gateway Config & Rate Limiting

| # | Issue | Status |
|---|-------|--------|
| 1 | Упростить JWT конфигурацию (AliasChoices, hardcode algorithm) | ✅ Done |
| 2 | Смягчить Rate Limiting для UX | ✅ Done |
| 3 | Endpoint-specific rate limits для Phase 2+ | Pending (Phase 2) |
| 4 | Документация JWT секретов в .env.example | Skipped (не нужно) |

## Architecture Alignment

| # | Issue | Status |
|---|-------|--------|
| 1 | Delivery public entrypoints bypass gateway (`/api/v1/deliveries/*`, `/ws/orders/{order_id}`) | ✅ Done |

---

## RequestLoggingMiddleware

| # | Issue | Status |
|---|-------|--------|
| 1 | X-Request-ID не передаётся downstream | ✅ Already done |
| 2 | Exception без X-Request-ID | ✅ Done |
| 3 | Дублирование log context | ✅ Done |
| 4 | Реальный client_ip за proxy | ✅ Done |
| 5 | Verbose logging mode | Pending (nice-to-have) |
| 6 | exc_info только в debug | ✅ Done |

---

## CircuitBreakerMiddleware

| # | Issue | Status |
|---|-------|--------|
| 1 | failure_count не сбрасывается | ✅ Done |
| 2 | Жёсткая привязка к URL | Pending (Phase 2) |
| 3 | HALF_OPEN race condition | Pending (Phase 2) |
| 4 | Thread safety для multi-worker | Pending (Production) |
| 5 | Per-service конфигурация | Pending (Phase 2+) |
| 6 | Prometheus metrics | ✅ Done |

---

## JWT Validator

| # | Issue | Status |
|---|-------|--------|
| 1 | Дублирование кода | ✅ Done |
| 2 | jwt_algorithm избыточен | ✅ Done |
| 3 | Недостаточное логирование | Pending |
| 4 | get_optional_user не различает ошибки | Pending (nice-to-have) |
| 5 | email может быть None | ✅ Done (теперь обязательный) |
| 6 | JTI blacklist | Pending (Phase 2) |
| 7 | Rate limiting на invalid tokens | Pending (Phase 2) |

---

## Rate Limiter

| # | Issue | Status |
|---|-------|--------|
| 1 | client_ip не учитывает proxy | ✅ Done |
| 2 | Дублирование кода | ✅ Done |
| 3 | Retry-After header | Pending (Phase 2) |
| 4 | decode_token_unverified caching | Pending (optimization) |
| 5 | remove_cooldown для admin | Pending (Phase 2) |
| 6 | Error messages дублирование | ✅ Done |
| 7 | Prometheus metrics | ✅ Done |


## 🔧 Technical Debt - Proxy Routes (API Gateway)

### 5. Нет retry логики при network errors
**Проблема:**
- При NetworkError сразу возвращается 502 Bad Gateway
- Временные сбои сети не обрабатываются
- Нет exponential backoff

**Решение:**
Добавить retry с tenacity (или полагаться на Circuit Breaker)

**Note:** Circuit Breaker уже есть, возможно достаточно

**Файлы:**
- `services/api-gateway/src/routes/proxy.py`

**Приоритет:** 🟡 Nice-to-have
**Effort:** 1 час
**Phase:** 2
**Status:** 🟡 Pending (needs analysis with Circuit Breaker)

---

### Summary - Proxy Routes Issues

| # | Issue | Priority | Effort | Phase |
|---|-------|----------|--------|-------|
| 5 | Нет retry логики | 🟡 Nice | 1 hr | 2 |

**Phase 2 focus:** Item #5
**Total recommended:** ~1 час (item 5)

---

## 🔧 Technical Debt - Resilience Strategy (Gateway)

### 1. Ретраи + Circuit Breaker (аналитика и тюнинг)
**Почему важно:**
- Ретраи могут усиливать нагрузку при деградации сервиса
- Circuit Breaker чувствителен к порогам и окнам наблюдения
- Неправильная настройка может ухудшить восстановление

**Что нужно определить:**
- Порог срабатывания (ошибки %) и window
- Совместимость с ретраями (какие ошибки/коды ретраить)
- Backoff стратегия (exponential + jitter)
- Где логически размещать (gateway-only или shared)
- Влияние на SLA и p95/p99

**Вывод:** отдельная аналитическая задача перед внедрением ретраев

**Приоритет:** 🟠 Medium
**Effort:** 2-4 часа
**Phase:** 2
**Status:** 🟡 Pending

---

## 🔧 Technical Debt - Phase 3 Integration Tests (Order Saga)

### 1. Integration tests can be skipped in docker profile on reused Postgres volumes
**Проблема:**
- Для `order-service` integration-тестов нужен `ORDER_SERVICE_TEST_DATABASE_URL`.
- На уже существующих локальных томах Postgres тестовая БД `order_service_test_db` может отсутствовать (init script отрабатывает только при первичной инициализации тома).
- В результате `pytest -m integration` для `order-service` даёт `skipped`, и это маскирует реальное состояние Phase 3.

**Что уже сделано:**
- Добавлен `ORDER_SERVICE_TEST_DATABASE_URL` в `test-runner` (`infrastructure/docker-compose.yml`).
- Добавлено создание `order_service_test_db` в `infrastructure/postgres/init-databases.sh` для новых инициализаций.

**Что осталось сделать:**
- Добавить явный preflight/auto-bootstrap test DB перед `make test-order` (или отдельной командой), чтобы на старых томах тесты не skip-ались.
- В CI/локальном пайплайне считать skip этих integration-тестов сигналом о некорректном окружении.

**Файлы:**
- `infrastructure/docker-compose.yml`
- `infrastructure/postgres/init-databases.sh`
- `services/order-service/tests/integration/*`
- `Makefile`

**Приоритет:** 🟠 Medium
**Effort:** 1-2 часа
**Phase:** 3
**Status:** 🟡 Pending

### 2. Долгие ожидания при `make test-*` в случае проблем окружения
**Проблема:**
- При недоступном Docker daemon или нездоровых зависимостях тестовые цели могли ждать несколько минут перед падением.

**Что уже сделано:**
- Добавлен fail-fast precheck `docker-ready` в Makefile.
- Сокращены и параметризованы ожидания `wait-http` (`WAIT_HTTP_RETRIES`, `WAIT_HTTP_SLEEP_SECONDS`).

**Что осталось сделать:**
- (Опционально) перевести ожидание сервисов на единый health-wait механизм compose/скрипт с агрегированным таймаутом.

**Приоритет:** 🟡 Nice-to-have
**Effort:** 0.5-1 час
**Phase:** 3/9
**Status:** 🟡 Pending

---

## 🔧 Technical Debt - Phase 8 Review Scope

### 1. Courier identity is still a mock dispatch pool, not a dedicated domain
**Проблема:**
- `delivery-service` теперь хранит и отдает `courier_id`, поэтому courier reviews работают.
- Но источник courier identity пока учебный: локально/в dev режиме он берется из
  конфигурируемого `DELIVERY_SERVICE_MOCK_COURIER_IDS`.
- Это закрывает контракт Phase 8, но не заменяет полноценный courier-domain/source of truth.

**Что уже сделано:**
- Реализован restaurant + courier review flow с проверкой владельца заказа и завершенной доставки.
- `delivery-service` assignment/read contract теперь возвращает `courier_id`.
- `review-service` переведен на общий target model (`restaurant` / `courier`).

**Что осталось сделать:**
- При появлении отдельного courier-domain заменить mock courier pool на реальный источник identity.
- При необходимости расширить analytics/read models агрегатами рейтингов по courier/restaurant.

**Файлы:**
- `services/delivery-service/src/domain/entities/assignment.py`
- `services/delivery-service/src/infrastructure/repositories/round_robin_courier_allocator.py`
- `services/delivery-service/src/interface/api/v1/routes/deliveries.py`
- `services/review-service/src/*`

**Приоритет:** 🟠 Medium
**Effort:** 1-2 дня
**Phase:** 8
**Status:** 🟡 Deferred Follow-up

---

## 🔧 Technical Debt - Assistant Proposals (Performance & Async Architecture)

> Ниже мои предложения как engineering follow-up после закрытия Phase 9.
> Это не зафиксированный roadmap scope, а рекомендованные улучшения по итогам e2e/load-проверок.

### 1. Order creation still uses a synchronous HTTP critical path
**Проблема:**
- `POST /api/v1/orders` сейчас держит клиентский HTTP-запрос открытым через весь orchestration flow.
- Реальный critical path проходит через `gateway -> order-service -> restaurant/payment/delivery`.
- Из-за этого latency заказа масштабируется хуже, чем у truly async workflow, и gateway timeout приходится подстраивать под saga duration.

**Почему это важно:**
- событийная архитектура даёт value в downstream side-effects, но не ускоряет сам request, пока заказ создаётся синхронно;
- under load bottleneck остаётся в order orchestration path, а не в consumer side-effects.

**Что предлагаю:**
- перевести `POST /api/v1/orders` на async contract (`202 Accepted`);
- возвращать `order_id` сразу после приёма команды;
- orchestration выполнять в background worker / event-driven pipeline;
- финальный статус заказа читать через `GET /orders/{id}` и/или websocket/event stream.

**Приоритет:** 🔴 High
**Effort:** 2-4 дня
**Phase:** 10+
**Status:** 🟡 Proposed by assistant

### 2. Kafka topic bootstrap is infrastructure-critical, but was not part of test/service startup
**Проблема:**
- `KAFKA_AUTO_CREATE_TOPICS_ENABLE=false`, но topics не гарантировались автоматически до первого боевого трафика;
- из-за этого producer/consumer path ловил `UnknownTopicOrPartitionError`;
- это ухудшало startup reliability и искажало load-тесты.

**Что уже сделано:**
- в `make test-e2e` / `make test-e2e-load` добавлен автоматический вызов `infrastructure/kafka/create-topics.sh`.

**Что осталось сделать:**
- оформить topic bootstrap как штатную часть локального/dev startup, а не только тестового пайплайна;
- решить, где должен жить source of truth для topics:
  - infra bootstrap;
  - init container / provisioning job;
  - declarative topic management.

**Приоритет:** 🟠 Medium
**Effort:** 1-2 часа
**Phase:** 10
**Status:** 🟡 Proposed by assistant

### 3. Readiness and liveness are still partially mixed for Kafka-backed services
**Проблема:**
- сервис может быть жив как HTTP/API process, но ещё не быть fully ready as Kafka consumer;
- при жёстком старте consumers в lifespan это приводило к startup crashes;
- сейчас startup-resilience улучшена retry-loop’ом, но health semantics всё ещё стоит разделить строже.

**Что уже сделано:**
- `notification-service` и `analytics-service` больше не падают при отсутствии Kafka topics на старте;
- consumer startup переведён на deferred background retry.

**Что осталось сделать:**
- явно развести liveness и readiness semantics;
- решить, должен ли `/health` отражать “process alive” или “all dependencies ready”;
- при необходимости выделить отдельные readiness endpoints для orchestration/compose.

**Приоритет:** 🟠 Medium
**Effort:** 0.5-1 день
**Phase:** 10
**Status:** 🟡 Proposed by assistant

### 4. Load smoke exists, but there is no real performance SLA yet
**Проблема:**
- текущий `make test-e2e-load` — это smoke-level guardrail на `10` concurrent orders;
- он полезен для регрессий, но не отвечает на вопрос о реальной производительности системы;
- нет явных целей по `p95`, throughput, consumer lag, recovery time.

**Что предлагаю:**
- зафиксировать performance budget для Phase 10+:
  - p95/p99 для `POST /orders`;
  - throughput для order creation;
  - consumer lag thresholds;
  - end-to-end time from order accepted to order confirmed;
- после этого расширить load tests с отдельным сценарием benchmark, а не смешивать его с функциональным e2e.

**Приоритет:** 🟠 Medium
**Effort:** 0.5-1 день на определение SLA, дальше отдельно по инструментам
**Phase:** 10+
**Status:** 🟡 Proposed by assistant

---

## 🔧 Technical Debt - Local Runtime Stability After Phase 10

### 1. Monitoring stack is up, but application stack is not restart-stable
**Проблема:**
- по факту локальный `make health` после остановки и повторного запуска окружения показывает, что monitoring stack healthy, но business stack не выходит в стабильное рабочее состояние;
- зафиксирован реальный runtime snapshot:
  - `PostgreSQL` down;
  - `Kafka` down;
  - `restaurant-service`, `order-service`, `notification-service`, `analytics-service`, `review-service`, `api-gateway` unhealthy;
  - `payment-service` и `delivery-service` stuck in `starting`;
- это означает, что текущий Compose/runtime нельзя считать надёжно восстанавливаемым после restart, даже если observability-компоненты уже поднялись.

**Почему это важно:**
- Phase 10 закрывает observability только частично, если сами сервисы не восстанавливаются предсказуемо;
- наличие Grafana/Prometheus без стабильного app stack создаёт ложное ощущение готовности;
- любой следующий phase/slice будет опираться на нестабильную локальную базу и давать шумные регрессии.

**Что уже выявлено:**
- health/startup semantics у инфраструктурных зависимостей всё ещё хрупкие;
- Kafka оставался bottleneck для зависимых сервисов при повторных запусках;
- у `payment-service` был реальный Docker/runtime defect: image не содержал `shared`, что приводило к `ModuleNotFoundError: shared`;
- часть сервисов уходит в долгий startup path (`migrations` / dependency wait), но не открывает HTTP readiness в ожидаемое время.

**Что осталось сделать:**
- довести Compose stack до гарантированно воспроизводимого cold start / restart сценария;
- отдельно проверить и стабилизировать:
  - PostgreSQL bootstrap и зависимости сервисов от него;
  - Kafka health/readiness и порядок старта Kafka-backed сервисов;
  - migrations/startup path для `order-service`, `review-service`, `payment-service`, `notification-service`, `analytics-service`, `api-gateway`;
- ввести явный acceptance criterion: после `make down && make up` и повторного `make health` весь обязательный application stack должен быть `healthy`, а не `starting/unhealthy`;
- после стабилизации синхронизировать docs/status, чтобы Phase 10 не выглядела operationally complete раньше времени.

**Файлы/зоны:**
- `infrastructure/docker-compose.yml`
- `scripts/check-health.sh`
- `services/*/Dockerfile`
- `services/*/src/main.py`
- `services/*/src/config.py`
- `PROGRESS.md`

**Приоритет:** 🔴 High
**Effort:** 1-2 дня на стабилизацию локального runtime + отдельное время на точечные сервисные дефекты
**Phase:** 10 follow-up
**Status:** ✅ Resolved

**Resolution:**
- root cause устранён: payment-service Dockerfile теперь копирует и ставит `shared` (`COPY shared` + `uv pip install -e /app/shared`), что убрало `ModuleNotFoundError: shared`;
- закреплён startup/health ordering сервисов;
- проверено после полной пересборки и чистого старта: весь стек (PostgreSQL, Kafka, ClickHouse, все доменные сервисы, api-gateway, monitoring) выходит в `healthy`;
- остаточный nice-to-have: строгий stop/start цикл на переиспользуемых postgres-томах (init-скрипт не повторяется на старом томе) — отдельный low-priority follow-up, не блокер.
