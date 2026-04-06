# Food Delivery Platform

Микросервисная платформа доставки еды с фокусом на надежность, масштабируемость и предсказуемые инженерные практики.

## Обзор

Текущее состояние репозитория:

- ✅ `api-gateway`
- ✅ `user-service`
- ✅ `restaurant-service`
- 🚧 `order-service` (saga orchestration, базовый API)
- ✅ `payment-service` (lifecycle + saga compatibility)
- ✅ `delivery-service` (contract lifecycle + tracking + gateway WS proxy)
- ✅ `notification-service` (event-driven mock email/push, Phase 6 completed)
- ⚪ `analytics-service`, `review-service` — в roadmap

## Архитектура

```text
Clients
  -> API Gateway (8000)
      -> User Service (8001)
      -> Restaurant Service (8002)
      -> Order Service (8003)
      -> Payment Service (8004, public payment API)
      -> Delivery Service (8005, public delivery API + WS)

Internal service-to-service:
Order Service (8003)
  -> Payment Service (8004, saga contract)
  -> Delivery Service (8005, saga contract)

Infra:
- PostgreSQL (service databases)
- Redis (rate limiting + token storage + Pub/Sub for WS fanout)
- Kafka + Kafka UI (event bus)
```

Ключевые принципы:

- единая точка входа через API Gateway;
- внутренние сервисные вызовы идут напрямую между сервисами;
- разделение сервисов и контрактов;
- Clean Architecture в доменных сервисах (`domain -> application -> infrastructure -> interface`);
- единые API-конвенции и формат ошибок.

## Коммуникационная модель

- Внешние клиенты (`web/mobile/courier app`) вызывают сервисы через API Gateway.
- Внутренние saga-шаги выполняются напрямую (`order-service -> payment-service`, `order-service -> delivery-service`).
- Kafka используется для надежных межсервисных событий.
- Redis Pub/Sub используется для real-time fanout в delivery tracking по WebSocket.

## Сервисы

| Service | Port | Status | Purpose |
|---|---:|---|---|
| API Gateway | 8000 | ✅ | JWT validation, rate limiting, proxying |
| User Service | 8001 | ✅ | registration, login, profile |
| Restaurant Service | 8002 | ✅ | restaurants and menu management |
| Order Service | 8003 | 🚧 | order creation and saga orchestration |
| Payment Service | 8004 | ✅ | payment reserve/confirm/refund/history + idempotency |
| Delivery Service | 8005 | ✅ | courier lifecycle + tracking (Phase 5 completed, contract-stage) |
| Notification Service | 8006 | ✅ | event-driven email/push delivery + notification history |
| Analytics Service | 8007 | ⚪ | planned |
| Review Service | 8008 | ⚪ | planned |

## Технологический стек

- Python 3.12, FastAPI, Pydantic, SQLAlchemy
- PostgreSQL, Redis, Kafka
- Docker / Docker Compose
- `uv` workspace
- pytest + pytest-asyncio
- Ruff, mypy, pre-commit

## Быстрый старт

```bash
# 1) Подготовить окружение
cp .env.example .env

# 2) Установить зависимости и инструменты
make dev-install

# 3) Поднять инфраструктуру и сервисы
make up

# 4) Проверить состояние
make health

# 5) Применить миграции
make migrate
```

## Полезные команды

```bash
make down
make logs
make clean
make kafka-topics

make test-all
make test-all-full
make test-unit
make test-integration
make test-e2e
make test-cov

make test-user
make test-user-unit
make test-user-integration
make test-gateway
make test-gateway-unit
make test-gateway-integration
make test-restaurant
make test-restaurant-unit
make test-restaurant-integration
make test-order
make test-order-unit
make test-order-integration
make test-payment
make test-payment-unit
make test-payment-integration
make test-delivery
make test-delivery-unit
make test-delivery-integration
make test-notification
make test-notification-unit

make dev-gateway
make dev-user
make dev-restaurant
make dev-order
make dev-payment
make dev-delivery
make dev-notification
```

`make test` запускает только repo-level тесты из `./tests` (если они есть).
`make test-all` запускает unit + integration по всем сервисам (без e2e).

## Структура репозитория

```text
food-delivery/
├── docs/
├── infrastructure/
├── scripts/
├── services/
├── shared/
├── tests/
├── Makefile
└── .env.example
```

## Документация

- `PROGRESS.md` — фактический статус фаз
- `DEVELOPMENT-ROADMAP.md` — high-level план развития
- `docs/API_CONVENTIONS.md` — API форматы и ошибки
- `docs/ENGINEERING_CONVENTIONS.md` — инженерные соглашения
- `docs/TECH_DEBT.md` — технический долг
- `docs/adr/` — архитектурные решения (ADR)
