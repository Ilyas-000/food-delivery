# Food Delivery Platform

Микросервисная платформа доставки еды с фокусом на надежность, масштабируемость и четкие инженерные правила.

## Содержание

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Спецификация и стандарты](#спецификация-и-стандарты)
- [Сервисы](#сервисы)
- [Технологический стек](#технологический-стек)
- [Инфраструктура и запуск](#инфраструктура-и-запуск)
- [Локальная разработка](#локальная-разработка)
- [Тестирование](#тестирование)
- [Структура репозитория](#структура-репозитория)
- [Документация](#документация)

---

## Обзор

Проект реализует базовую платформу доставки еды на микросервисной архитектуре. Уже доступны API Gateway и User Service, остальные сервисы описаны в roadmap и добавляются по фазам.

## Архитектура

```
Clients → API Gateway → User Service → PostgreSQL
                        ↘ Redis (rate limiting)

Kafka (event bus) подключается по мере ввода сервисов
```

Ключевые принципы:
- единая точка входа через API Gateway
- отдельные базы данных на сервис
- строгие границы слоев (domain → application → infrastructure → interface)
- единые API-конвенции и типовые ошибки

## Спецификация и стандарты

- API форматы и ошибки: `docs/API_CONVENTIONS.md`
- Инженерные правила: `docs/ENGINEERING_CONVENTIONS.md`

## Сервисы

| Сервис | Порт | Статус | Назначение |
|--------|------|--------|------------|
| API Gateway | 8000 | ✅ Готов | JWT, rate limiting, routing |
| User Service | 8001 | ✅ Готов | регистрация, логин, профиль |
| Restaurant Service | 8002 | 🚧 План | рестораны, меню |
| Order Service | 8003 | 🚧 В работе | заказы, saga |
| Payment Service | 8004 | 🚧 План | платежи |
| Delivery Service | 8005 | 🚧 План | доставка, трекинг |
| Notification Service | 8006 | 🚧 План | уведомления |
| Analytics Service | 8007 | 🚧 План | аналитика |
| Review Service | 8008 | 🚧 План | отзывы |

## Технологический стек

- Python 3.12, FastAPI, Pydantic, SQLAlchemy
- PostgreSQL, Redis
- Kafka (event bus)
- Docker, Docker Compose
- pytest + pytest-asyncio

## Инфраструктура и запуск

### Требования

- Docker
- Docker Compose
- Python 3.12+ (для локальной разработки)
- Make

### Быстрый старт

```bash
# 1) Подготовка окружения (создает .env при необходимости)
make setup-dev

# 2) Запуск инфраструктуры и сервисов
make up

# 3) Проверка
make health
```

### Полезные команды

```bash
make down        # остановить сервисы
make logs        # смотреть логи
make clean       # удалить контейнеры/тома/кеши
make migrate     # миграции БД
make seed        # сидирование
make kafka-topics # создать топики Kafka
```

## Локальная разработка

Запуск сервисов без Docker:

```bash
# Инфраструктура в Docker
make up

# User Service локально
make dev-user

# API Gateway локально
make dev-gateway
```

Если запускаешь сервисы локально, убедись, что переменные в окружении указывают на localhost:
- `POSTGRES_HOST=localhost`
- `GATEWAY_REDIS_HOST=localhost`
- `GATEWAY_USER_SERVICE_URL=http://localhost:8001`

## Тестирование

```bash
make test           # тесты в корне (если есть)
make test-all       # тесты во всех сервисах
make test-user      # тесты User Service
make test-gateway   # тесты API Gateway
```

Для интеграционных тестов user-service нужен `USER_SERVICE_TEST_DATABASE_URL`.

## Структура репозитория

```
food-delivery/
├── docs/                 # правила, ADR, техдолг
├── infrastructure/       # docker-compose, init scripts
├── scripts/              # setup, health, migrate, seed
├── services/             # микросервисы
├── shared/               # общие утилиты и контракты
├── tests/                # repo-level tests (если есть)
├── Makefile
└── .env.example
```

## Документация

- `docs/API_CONVENTIONS.md` — правила API и форматы ошибок
- `docs/ENGINEERING_CONVENTIONS.md` — инженерные правила
- `docs/TECH_DEBT.md` — технический долг
- `docs/adr/` — архитектурные решения
- `DEVELOPMENT-ROADMAP.md` — план фаз
- `PROGRESS.md` — текущий статус
