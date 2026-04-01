# Food Delivery Platform

Микросервисная платформа доставки еды с фокусом на надежность, масштабируемость и предсказуемые инженерные практики.

## Обзор

Текущее состояние репозитория:

- ✅ `api-gateway`
- ✅ `user-service`
- ✅ `restaurant-service`
- 🚧 `order-service` (saga orchestration, базовый API)
- 🚧 `payment-service` (saga contract)
- 🚧 `delivery-service` (saga contract)
- ⚪ `notification-service`, `analytics-service`, `review-service` — в roadmap

## Архитектура

```text
Clients
  -> API Gateway (8000)
      -> User Service (8001)
      -> Restaurant Service (8002)
      -> Order Service (8003)
           -> Payment Service (8004, reservation contract)
           -> Delivery Service (8005, assignment contract)

Infra:
- PostgreSQL (service databases)
- Redis (rate limiting + token storage)
- Kafka + Kafka UI (event bus)
```

Ключевые принципы:

- единая точка входа через API Gateway;
- разделение сервисов и контрактов;
- Clean Architecture в доменных сервисах (`domain -> application -> infrastructure -> interface`);
- единые API-конвенции и формат ошибок.

## Сервисы

| Service | Port | Status | Purpose |
|---|---:|---|---|
| API Gateway | 8000 | ✅ | JWT validation, rate limiting, proxying |
| User Service | 8001 | ✅ | registration, login, profile |
| Restaurant Service | 8002 | ✅ | restaurants and menu management |
| Order Service | 8003 | 🚧 | order creation and saga orchestration |
| Payment Service | 8004 | 🚧 | payment reservation/release contract |
| Delivery Service | 8005 | 🚧 | courier assignment/cancel contract |
| Notification Service | 8006 | ⚪ | planned |
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
make test-unit
make test-integration
make test-e2e
make test-cov

make test-user
make test-gateway
make test-restaurant
make test-order
make test-payment
make test-delivery

make dev-gateway
make dev-user
make dev-restaurant
make dev-order
make dev-payment
make dev-delivery
```

`make test` запускает только repo-level тесты из `./tests` (если они есть).

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
