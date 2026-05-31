# Food Delivery Platform

Backend-платформа доставки еды на Python 3.12 и FastAPI. Репозиторий устроен как `uv` workspace: отдельные сервисы лежат в `services/`, общие инфраструктурные утилиты и контракты событий — в `shared/`.

## Архитектура

```text
Clients
  -> API Gateway (8000)
      -> User Service (8001)
      -> Restaurant Service (8002)
      -> Order Service (8003)
      -> Payment Service (8004)
      -> Delivery Service (8005)
      -> Analytics Service (8007)
      -> Review Service (8008)

Internal service calls:
Order Service
  -> Restaurant Service (menu validation)
  -> Payment Service (reserve/release)
  -> Delivery Service (assign/cancel courier)

Review Service
  -> Order Service (order ownership)
  -> Delivery Service (delivery status and courier id)

Kafka consumers:
Notification Service (8006)
Analytics Service (8007)

Infrastructure:
- PostgreSQL for service-owned databases
- Redis for refresh tokens, gateway rate limiting, and delivery WebSocket fanout
- Kafka for domain and operational events
- ClickHouse for analytics read storage
- Prometheus, Alertmanager, Grafana, Loki, Promtail for the monitoring profile
```

Внешний HTTP и WebSocket трафик для клиентских доменных API проходит через API Gateway. Внутренние orchestration-вызовы выполняются напрямую между сервисами, потому что gateway отвечает за north-south traffic, а не за сервисную координацию.

Доменные сервисы используют Clean Architecture: `domain`, `application`, `infrastructure`, `interface`. Домен не зависит от FastAPI, SQLAlchemy, Kafka или Redis; адаптеры инфраструктуры реализуют интерфейсы application-слоя.

## Сервисы

| Service | Port | Назначение |
|---|---:|---|
| API Gateway | 8000 | JWT validation, rate limiting, circuit breaker, REST/WS proxy |
| User Service | 8001 | регистрация, login, refresh/logout, профиль пользователя |
| Restaurant Service | 8002 | рестораны, меню, доступность позиций, поиск по фильтрам |
| Order Service | 8003 | создание заказа и синхронная saga-оркестрация |
| Payment Service | 8004 | резерв, release, confirm, refund, история платежей |
| Delivery Service | 8005 | назначение курьера, статус доставки, WebSocket tracking |
| Notification Service | 8006 | email/push уведомления по событиям Kafka |
| Analytics Service | 8007 | ingestion событий Kafka, ClickHouse, отчётные API |
| Review Service | 8008 | отзывы о ресторанах и курьерах, сводные рейтинги |

## Технологии

- Python 3.12, FastAPI, Pydantic
- SQLAlchemy 2.0, Alembic, PostgreSQL
- Redis, Kafka, ClickHouse
- Prometheus, Alertmanager, Grafana, Loki, Promtail
- Docker Compose
- pytest, pytest-asyncio, Ruff, mypy, pre-commit

## Быстрый старт

```bash
make setup-dev
make dev-install
make up
make health
```

`make setup-dev` готовит локальную конфигурацию и каталоги, `make up` поднимает инфраструктуру и сервисы через Docker Compose, `make health` проверяет HTTP health endpoints.

## Команды

```bash
make up                 # поднять сервисы
make down               # остановить сервисы
make logs               # показать логи контейнеров
make health             # проверить health endpoints
make migrate            # применить миграции
make seed               # загрузить seed data
make monitoring-up      # поднять Prometheus, Grafana, Loki, Alertmanager
make monitoring-down    # остановить monitoring profile
```

```bash
make test               # repo-level tests
make test-all           # unit + integration по всем сервисам
make test-all-full      # unit + integration + e2e
make test-unit          # unit по всем сервисам
make test-integration   # integration по всем сервисам
make test-e2e           # end-to-end tests
make test-cov           # coverage
```

Для отдельного сервиса:

```bash
make test-order
make test-order-unit
make test-order-integration
make dev-order
```

Поддерживаемые имена: `user`, `gateway`, `restaurant`, `order`, `payment`, `delivery`, `notification`, `analytics`, `review`.

## Репозиторий

```text
food-delivery/
├── docs/             # API conventions, engineering conventions, ADR, tech debt
├── infrastructure/   # Docker Compose, Kafka/Postgres bootstrap, monitoring config
├── scripts/          # setup, health checks, migrations, seed data, test matrix
├── services/         # FastAPI services
├── shared/           # shared events, Kafka/Redis/JWT helpers, observability
├── tests/            # repo-level e2e tests
├── Makefile
└── pyproject.toml
```

## Monitoring

Monitoring profile запускается отдельно:

```bash
make monitoring-up
```

Prometheus скрейпит `/metrics` у gateway и сервисов. Grafana получает datasources и dashboard provisioning из `infrastructure/docker/grafana`. Loki и Promtail собирают stdout/stderr контейнеров. Корреляция запросов построена на `X-Request-ID` и `X-Correlation-ID`.

## Документация

- [docs/API_CONVENTIONS.md](docs/API_CONVENTIONS.md) — HTTP, WebSocket, ошибки, пагинация
- [docs/ENGINEERING_CONVENTIONS.md](docs/ENGINEERING_CONVENTIONS.md) — инженерные правила проекта
- [docs/TECH_DEBT.md](docs/TECH_DEBT.md) — открытый технический долг
- [docs/adr/](docs/adr/) — architecture decision records
- [CONTRIBUTING.md](CONTRIBUTING.md) — правила контрибьютинга
