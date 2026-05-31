# Engineering Conventions

Документ фиксирует инженерные правила проекта. Он описывает текущее целевое поведение кода, а не план будущих работ.

## Архитектурные границы

- `domain` содержит сущности, value objects и доменные исключения.
- `application` содержит use cases, DTO и интерфейсы портов.
- `infrastructure` реализует порты application-слоя: БД, Kafka, Redis, HTTP clients.
- `interface` содержит FastAPI routes, dependencies, exception handlers, WebSocket endpoints и consumers.
- Импорты направлены внутрь: `interface -> application -> domain`, `infrastructure -> application -> domain`.
- `domain` и `application` не импортируют FastAPI, SQLAlchemy, Redis, Kafka, HTTP-клиенты и settings.

## Межсервисная коммуникация

- Внешний north-south traffic проходит через API Gateway.
- Внутренний east-west traffic выполняется напрямую между сервисами.
- Saga-шаги Order Service используют прямые HTTP-контракты Restaurant, Payment и Delivery Service.
- Kafka используется для доменных и операционных событий.
- Redis Pub/Sub используется для низколатентного WebSocket fanout, но не заменяет Kafka для событий, которые нужно хранить и переигрывать.

## Данные

- PostgreSQL используется как primary storage для сервисов, у которых есть персистентные write-модели.
- Сервис владеет своей схемой и миграциями; межсервисные foreign key не создаются.
- ClickHouse используется для аналитической read-модели.
- In-memory backend допустим для сервиса только как явно описанное ограничение или тестовый режим.

## События

- Kafka topic совпадает с `event_type`: `{service}.{aggregate}.{action}`.
- Pydantic-контракты событий лежат в `shared/src/shared/events`.
- События публикуются после изменения состояния, но текущая реализация не гарантирует atomic write + publish без outbox.
- Обработчики событий должны быть идемпотентными: повторная доставка не должна создавать некорректное состояние.

## Конфигурация

- Runtime-настройки читаются через Pydantic Settings.
- Сервисные переменные используют префикс конкретного сервиса: `USER_SERVICE_`, `ORDER_SERVICE_`, `GATEWAY_` и т.д.
- Общие настройки инфраструктуры используют отдельные префиксы (`POSTGRES_`, `KAFKA_`, `CLICKHOUSE_`).
- Host, port, credentials, feature flags и backend selectors не хардкодятся в use cases.

## Логирование и трассировка

- Для структурированных логов используется `structlog`.
- На границах сервиса логируются request id, correlation id, метод, путь, статус и длительность.
- Бизнес-логи пишутся в точках смены состояния, а не внутри каждого вспомогательного вызова.
- `X-Request-ID` и `X-Correlation-ID` сохраняются при проксировании и внутренних HTTP-вызовах.

## Метрики

- HTTP-метрики Prometheus публикуются на `/metrics`.
- Общие helpers находятся в `shared/src/shared/observability`.
- Сервис-специфичные метрики остаются рядом с владельцем поведения: например, rate limiting и circuit breaker в gateway.

## API

- Новые endpoints следуют [API_CONVENTIONS.md](API_CONVENTIONS.md).
- Pydantic schemas в `interface` отвечают за контракт HTTP, DTO в `application` — за входы и выходы use cases.
- Доменные ошибки мапятся в HTTP в exception handlers.

## Тесты

- Unit-тесты проверяют domain и application без внешней инфраструктуры.
- Integration-тесты проверяют реальные адаптеры: БД, HTTP-клиенты, Kafka/Redis при необходимости.
- E2E-тесты идут через API Gateway и покрывают пользовательский поток.
- `conftest.py` сервиса подключает `shared.testing.pytest_summary`, если сервис использует общий pytest summary.

## Технический долг

Временный workaround должен иметь короткое описание ограничения в [TECH_DEBT.md](TECH_DEBT.md). Закрытые пункты из файла удаляются.
