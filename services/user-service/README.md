# User Service

Сервис пользователей и аутентификации. Отвечает за регистрацию, login, refresh/logout и профиль пользователя.

## Назначение

- Регистрация пользователя.
- Login с выдачей access/refresh JWT.
- Refresh access token.
- Logout с ревокацией refresh token.
- Чтение и обновление профиля.
- Роли пользователя: customer, courier, restaurant owner, admin.

## API

### Health

- `GET /health`
- `GET /metrics`

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Users

- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/{user_id}`

## Хранилища

- PostgreSQL: пользователи и профильные данные.
- Redis: refresh-token storage.

## Запуск

```bash
make up
curl http://localhost:8001/health
```

Локальный запуск только сервиса:

```bash
make dev-user
```

## Конфигурация

Настройки читаются из `services/user-service/src/config.py` с префиксом `USER_SERVICE_`. Общие параметры PostgreSQL читаются через `POSTGRES_`.

Ключевые группы:
- PostgreSQL database/user/password;
- JWT secret, algorithm, token TTL;
- bcrypt rounds;
- Redis host/port/db;
- CORS origins.

## Миграции

```bash
cd services/user-service
alembic upgrade head
```

## Тестирование

```bash
make test-user
make test-user-unit
make test-user-integration
```

## Ограничения

- Kafka-события пользователей описаны в shared-контрактах, но публикация из User Service не подключена.
- JTI blacklist для более строгой JWT revocation остаётся техническим долгом.
