# API Gateway

Единая точка входа для микросервисов Food Delivery.

## Возможности

- Reverse proxy для:
  - User Service (`/api/v1/auth/*`, `/api/v1/users/*`)
  - Restaurant Service (`/api/v1/restaurants/*`)
  - Order Service (`/api/v1/orders/*`)
- JWT валидация для protected маршрутов
- Rate limiting на Redis (global auth, login, refresh)
- Circuit breaker middleware
- Request logging middleware с `X-Request-ID`
- Health checks: `/health`, `/ready`

## Архитектура

```text
Client
  -> API Gateway
      -> User Service
      -> Restaurant Service
      -> Order Service
```

## Запуск

### Через Compose (рекомендуется)

```bash
make up
curl http://localhost:8000/health
```

### Локально

```bash
# инфраструктура в docker
make up

# gateway локально
make dev-gateway
```

Для локального запуска проверь значения в окружении:
- `GATEWAY_REDIS_HOST=localhost`
- `GATEWAY_USER_SERVICE_URL=http://localhost:8001`
- `GATEWAY_RESTAURANT_SERVICE_URL=http://localhost:8002`
- `GATEWAY_ORDER_SERVICE_URL=http://localhost:8003`

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

### Restaurants
- `POST /api/v1/restaurants` (protected)
- `GET /api/v1/restaurants`
- `GET /api/v1/restaurants/{restaurant_id}`
- `PUT/PATCH /api/v1/restaurants/{restaurant_id}` (protected)
- `DELETE /api/v1/restaurants/{restaurant_id}` (protected)
- `GET /api/v1/restaurants/{restaurant_id}/menu`
- `POST /api/v1/restaurants/{restaurant_id}/menu-items` (protected)
- `GET /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}`
- `PUT/PATCH /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}` (protected)
- `PATCH /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}/availability` (protected)
- `DELETE /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}` (protected)

### Orders (protected)
- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`

## Конфигурация

Смотри `.env.example`. Ключевые параметры:
- `GATEWAY_JWT_SECRET_KEY`
- `GATEWAY_REDIS_HOST`, `GATEWAY_REDIS_PORT`, `GATEWAY_REDIS_DB`
- `GATEWAY_USER_SERVICE_URL`
- `GATEWAY_RESTAURANT_SERVICE_URL`
- `GATEWAY_ORDER_SERVICE_URL`
- `GATEWAY_RATE_LIMIT_ENABLED`

## Ограничения текущей фазы

- Прямые proxy-роуты к Payment/Delivery из gateway пока не добавлены.
- Payment/Delivery используются Order Service в saga HTTP flow.

## Тестирование

```bash
make test-gateway
```
