# User Service

Сервис управления пользователями и аутентификации.

## Основные функции

- Регистрация и логин
- JWT access/refresh токены
- Logout с ревокацией refresh token
- Профиль пользователя (получение/обновление)
- Роли: Customer, Courier, RestaurantOwner, Admin

## Технологии

- FastAPI
- SQLAlchemy 2.0 (async)
- Alembic
- PostgreSQL
- Redis
- JWT, bcrypt

## Структура проекта (Clean Architecture)

```
src/
├── domain/
├── application/
├── infrastructure/
└── interface/
```

## Запуск

### Через Docker Compose (рекомендуется)

```bash
make up
curl http://localhost:8001/health
```

Если нужно поднять только сервис:

```bash
docker-compose --env-file .env -f infrastructure/docker-compose.yml up user-service
```

### Локально (для разработки)

```bash
# инфраструктура в Docker
make up

# сервис локально
make dev-user
```

## Переменные окружения

Большинство переменных используют prefix `USER_SERVICE_`.

Ключевые настройки:
- `POSTGRES_HOST` (локально: `localhost`, в Docker: `postgres`)
- `POSTGRES_PORT`
- `USER_SERVICE_DB_NAME/USER/PASSWORD`
- `USER_SERVICE_JWT_SECRET_KEY`
- `USER_SERVICE_REDIS_HOST` (локально: `localhost`, в Docker: `redis`)

Смотри `.env.example` для полного списка.

## API Endpoints

### Health
- `GET /health`

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Users
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/{user_id}` (admin)

## Тестирование

```bash
make test-user
```

## Миграции

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Статус

### Реализовано
- Регистрация, логин, refresh, logout
- Профиль пользователя (получение/обновление)
- Доменные проверки Email/Password
- Миграции и репозитории
- Тесты (unit + integration)

### Отложено / Backlog
- Kafka события (UserCreated/UserUpdated)
- Redis кеширование
