# Contributing

Документ фиксирует рабочие правила для изменений в Food Delivery Platform.

## Подготовка

Требования:
- Python 3.12
- Docker и Docker Compose
- `uv`
- Git

Базовая настройка:

```bash
make setup-dev
make dev-install
make health
```

## Ветки и коммиты

Ветка создаётся от `main`:

```bash
git checkout -b feat/order-cancellation
```

Префиксы веток:
- `feat/` — новая функциональность
- `fix/` — исправление дефекта
- `refactor/` — изменение внутренней структуры без изменения поведения
- `docs/` — документация
- `test/` — тесты
- `chore/` — обслуживание проекта

Коммиты оформляются в формате Conventional Commits:

```bash
feat(order-service): add cancellation endpoint
fix(api-gateway): preserve correlation id on proxy errors
docs(adr): record database ownership decision
```

Допустимые типы: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`.

## Проверки перед PR

```bash
make format
make lint
make type-check
make test-all
```

Для изменений в критическом межсервисном потоке дополнительно запускаются e2e-тесты:

```bash
make test-e2e
```

## Стиль кода

- Python 3.12.
- Type hints обязательны для функций и публичных методов.
- Публичные методы документируются Google-style docstrings.
- Форматирование и linting выполняются Ruff.
- Длина строки: 100 символов.
- Кавычки: двойные.
- Импорты: абсолютные (`from src...`, `from shared...`), без относительных импортов между слоями.

## Архитектурные границы

Каждый доменный сервис сохраняет структуру:

```text
src/
├── domain/           # entities, value objects, domain exceptions
├── application/      # use cases, DTO, interfaces
├── infrastructure/   # database, Kafka, Redis, HTTP clients
└── interface/        # FastAPI routes, dependencies, consumers
```

Правило зависимостей:

```text
interface -> application -> domain
infrastructure -> application -> domain
```

`domain` не импортирует FastAPI, SQLAlchemy, Redis, Kafka, HTTP-клиенты или настройки окружения. `application` объявляет интерфейсы, `infrastructure` реализует их.

## Тесты

Основные команды:

```bash
make test-all
make test-unit
make test-integration
make test-e2e
make test-cov
```

Тесты именуются `test_*.py`, функции — `test_*`. Для async-кода используется `pytest-asyncio`. Маркеры: `unit`, `integration`, `e2e`, `slow`.

Порог покрытия в конфигурации проекта: 80%.

## Pull Request

Перед открытием PR:
- проверки форматирования, linting, typing и тестов проходят локально;
- документация обновлена вместе с изменением публичного поведения;
- для архитектурных решений добавлен или обновлён ADR;
- технический долг зафиксирован в [docs/TECH_DEBT.md](docs/TECH_DEBT.md), если изменение оставляет осознанное ограничение.

Описание PR должно отвечать на четыре вопроса:
- что изменилось;
- почему это нужно;
- как проверено;
- какие ограничения или follow-up остались.
