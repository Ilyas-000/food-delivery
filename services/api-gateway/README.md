# API Gateway

Единая точка входа для микросервисов Food Delivery.

## Возможности

- Reverse proxy к User Service
- JWT валидация
- Rate limiting (Redis)
- Circuit breaker
- CORS
- Health checks: `/health`, `/ready`

## Архитектура

```
Client → API Gateway → User Service (8001)
```

## Запуск

### Через Docker Compose (рекомендуется)

```bash
make up
curl http://localhost:8000/health
```

Если нужно поднять только gateway:

```bash
docker-compose --env-file .env -f infrastructure/docker-compose.yml up api-gateway
```

### Локально

```bash
make up
make dev-gateway
```

Для локального запуска убедись, что переменные указывают на localhost:
- `GATEWAY_REDIS_HOST=localhost`
- `GATEWAY_USER_SERVICE_URL=http://localhost:8001`

## Основные endpoints

### Health
- `GET /health`
- `GET /ready`

### Auth (public)
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Users (protected)
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/{user_id}`

## Конфигурация

Смотри `.env.example`. Ключевые параметры:
- `GATEWAY_JWT_SECRET_KEY`
- `GATEWAY_REDIS_HOST`
- `GATEWAY_USER_SERVICE_URL`
- `GATEWAY_RATE_LIMIT_ENABLED`

## Тестирование

```bash
make test-gateway
```
