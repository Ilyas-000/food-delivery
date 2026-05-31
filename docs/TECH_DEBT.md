# Technical Debt

Файл содержит только открытые пункты. Закрытые задачи удаляются, чтобы документ оставался списком актуальной работы.

## API Gateway

### Endpoint-specific rate limits

**Проблема:** rate limiting детально настроен для auth flow, но не для всех доменных endpoints. Нагрузка на `orders`, `payments`, `reviews` и analytics routes пока ограничивается более общими правилами.

**Что сделать:** определить лимиты по endpoint-группам и вынести настройки в явные параметры gateway.

**Зона:** `services/api-gateway/src/middleware/rate_limiter.py`, `services/api-gateway/src/config.py`

**Приоритет:** Medium

### Proxy retry policy

**Проблема:** transient network errors сейчас приводят к `502 Bad Gateway` без retry. Слепое добавление retry может усилить нагрузку на деградирующий сервис, поэтому нужна политика по типам ошибок и методам.

**Что сделать:** описать retry matrix, совместить её с circuit breaker, добавить exponential backoff с jitter только для безопасных или идемпотентных операций.

**Зона:** `services/api-gateway/src/routes/proxy.py`, `services/api-gateway/src/middleware/circuit_breaker.py`

**Приоритет:** Medium

### Circuit breaker tuning

**Проблема:** circuit breaker использует базовую конфигурацию и хранит состояние в процессе. Multi-worker режим и разные профили downstream-сервисов требуют отдельного анализа.

**Что сделать:** добавить per-service настройки, проверить race conditions в half-open состоянии, определить поведение для multi-worker deployment.

**Зона:** `services/api-gateway/src/middleware/circuit_breaker.py`

**Приоритет:** Medium

### Rate limit response headers

**Проблема:** не все rate-limit ответы возвращают полный набор headers вроде `Retry-After` и remaining counters.

**Что сделать:** унифицировать headers для throttled responses.

**Зона:** `services/api-gateway/src/middleware/rate_limiter.py`

**Приоритет:** Low

## Authentication

### Refresh token blacklist by JTI

**Проблема:** logout и refresh-token flow используют Redis-backed storage, но отдельная blacklist по JTI может понадобиться для более строгой ревокации.

**Что сделать:** определить модель хранения JTI, TTL и поведение при повторном refresh.

**Зона:** `services/user-service/src/infrastructure/cache/refresh_token_repository.py`, `services/api-gateway/src/middleware/jwt_validator.py`

**Приоритет:** Medium

### Optional auth error semantics

**Проблема:** optional auth paths не всегда различают отсутствие токена, истёкший токен и неверную подпись. Для публичных endpoints это допустимо, но диагностика и audit logs теряют точность.

**Что сделать:** разделить результат optional validation на `anonymous`, `authenticated`, `invalid`.

**Зона:** `services/api-gateway/src/middleware/jwt_validator.py`

**Приоритет:** Low

## Order Saga

### Synchronous order creation critical path

**Проблема:** `POST /api/v1/orders` держит HTTP-запрос открытым на весь flow `gateway -> order-service -> restaurant/payment/delivery`. Latency заказа равна сумме удалённых вызовов и компенсаций при сбое.

**Что сделать:** рассмотреть асинхронный контракт `202 Accepted`: заказ создаётся в начальном состоянии, orchestration выполняется background worker'ом, статус читается через `GET /orders/{id}` или отдельный stream.

**Зона:** `services/order-service/src/application/use_cases/create_order.py`, `services/order-service/src/infrastructure/saga/*`, `tests/e2e/test_order_journey.py`

**Приоритет:** High

### Saga state persistence

**Проблема:** Order Service сохраняет заказ, но не сохраняет отдельный журнал состояния saga-шагов. При падении процесса между шагами восстановление ограничено текущим статусом заказа и side effects downstream-сервисов.

**Что сделать:** добавить persistable saga state или outbox-driven orchestration с явным recovery path.

**Зона:** `services/order-service/src/application/dto/order.py`, `services/order-service/src/application/use_cases/create_order.py`, `services/order-service/src/infrastructure/database`

**Приоритет:** High

## Events

### Outbox for reliable Kafka publishing

**Проблема:** сервисы публикуют Kafka-события best-effort после изменения состояния. Если запись в БД прошла, а publish упал, событие может быть потеряно.

**Что сделать:** внедрить transactional outbox в сервисах с PostgreSQL-backed state и dispatcher, который публикует события в Kafka с retry.

**Зона:** `services/order-service`, `services/restaurant-service`, `services/review-service`, `shared/src/shared/events`

**Приоритет:** High

### Consumer readiness

**Проблема:** сервис может отвечать на `/health`, но Kafka consumer ещё находится в retry startup loop. Это корректно для liveness, но не отражает готовность ingest/notification функций.

**Что сделать:** развести liveness и readiness для Kafka-backed сервисов.

**Зона:** `services/notification-service/src/main.py`, `services/analytics-service/src/main.py`

**Приоритет:** Medium

## Delivery

### Persistent delivery storage

**Проблема:** Delivery Service использует in-memory assignment repository. После рестарта теряется состояние назначений и tracking lifecycle.

**Что сделать:** добавить PostgreSQL-backed repository и миграции для assignment state.

**Зона:** `services/delivery-service/src/infrastructure/repositories`, `services/delivery-service/src/domain/entities/assignment.py`

**Приоритет:** High

### Courier domain

**Проблема:** `courier_id` выбирается из mock-пула в Delivery Service. Для отзывов и analytics этого достаточно как контракт, но нет отдельного источника правды по курьерам, доступности и сменам.

**Что сделать:** выделить courier domain или интеграцию с сервисом курьеров, затем заменить mock allocator.

**Зона:** `services/delivery-service/src/infrastructure/repositories/round_robin_courier_allocator.py`, `services/review-service/src/infrastructure/clients/review_validation_clients.py`

**Приоритет:** Medium

## Testing

### Integration test database bootstrap on reused volumes

**Проблема:** PostgreSQL init scripts выполняются только при первом создании volume. На уже существующем volume тестовая БД может отсутствовать, и integration-тесты получают skip вместо полезного failure.

**Что сделать:** добавить явный bootstrap test databases перед integration matrix и считать unexpected skip ошибкой окружения.

**Зона:** `scripts/bootstrap-test-databases.sh`, `infrastructure/postgres/init-databases.sh`, `Makefile`

**Приоритет:** Medium

### Performance budgets

**Проблема:** есть e2e load smoke на конкурентное создание заказов, но нет зафиксированных целей по p95/p99, throughput, consumer lag и recovery time.

**Что сделать:** определить performance budget и отделить benchmark-сценарии от функционального e2e.

**Зона:** `tests/e2e/test_order_journey.py`, `scripts/run-test-matrix.sh`

**Приоритет:** Medium
