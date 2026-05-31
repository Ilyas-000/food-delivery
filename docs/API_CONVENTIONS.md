# API Conventions

Документ задаёт публичные HTTP и WebSocket соглашения для сервисов Food Delivery Platform.

## Базовые правила

- Публичный HTTP API версионируется через `/api/v1`.
- Внешний клиентский трафик проходит через API Gateway.
- JSON используется для запросов и ответов HTTP API.
- Имена полей в JSON: `snake_case`.
- Временные метки передаются в ISO 8601 с UTC timestamp.
- Защищённые маршруты принимают `Authorization: Bearer <jwt>`.
- `X-Request-ID` и `X-Correlation-ID` пробрасываются через gateway и downstream-сервисы.

## URL

```text
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{sub_resource}
```

Ресурсы именуются существительными во множественном числе:

```http
GET  /api/v1/users/me
GET  /api/v1/restaurants
POST /api/v1/orders
GET  /api/v1/reviews/restaurants/{restaurant_id}/rating
```

Для составных ресурсов используется `kebab-case`:

```http
POST  /api/v1/restaurants/{restaurant_id}/menu-items
PATCH /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}/availability
```

Глубокая вложенность заменяется query-параметрами:

```http
GET /api/v1/reviews?target_type=restaurant&target_id={restaurant_id}
```

## HTTP-методы

| Метод | Использование |
|---|---|
| `GET` | чтение ресурса или списка |
| `POST` | создание ресурса или запуск команды |
| `PUT` | полная замена ресурса |
| `PATCH` | частичное обновление ресурса |
| `DELETE` | удаление, деактивация или компенсация |

## HTTP-статусы

| Код | Смысл |
|---:|---|
| `200` | успешное чтение или обновление с телом ответа |
| `201` | ресурс создан |
| `202` | команда принята в асинхронную обработку |
| `204` | операция выполнена, тело не возвращается |
| `400` | синтаксически некорректный запрос |
| `401` | отсутствует или невалиден JWT |
| `403` | прав недостаточно |
| `404` | ресурс не найден |
| `409` | конфликт состояния или дубликат |
| `422` | нарушение бизнес-правила |
| `429` | превышен rate limit |
| `500` | непредвиденная ошибка сервиса |
| `502` | upstream-сервис вернул ошибку или недоступен |
| `503` | сервис временно не готов |
| `504` | таймаут upstream-сервиса |

## Ошибки

Стандартный формат:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "7af7d2cb-09f7-4a8f-97b5-4bb08b6d5f3c",
    "timestamp": "2026-05-31T12:34:56.789Z"
  }
}
```

Базовые коды:

| Code | HTTP |
|---|---:|
| `VALIDATION_ERROR` | 400 |
| `UNAUTHORIZED` | 401 |
| `FORBIDDEN` | 403 |
| `NOT_FOUND` | 404 |
| `CONFLICT` | 409 |
| `BUSINESS_RULE_VIOLATION` | 422 |
| `RATE_LIMIT_EXCEEDED` | 429 |
| `INTERNAL_ERROR` | 500 |
| `SERVICE_UNAVAILABLE` | 503 |

Доменные исключения мапятся в HTTP на уровне `interface/api/exception_handlers.py` конкретного сервиса.

## Списки и пагинация

Списочные endpoints принимают `limit`/`offset` или `page`/`page_size`; выбранный формат должен быть стабильным внутри сервиса.

```http
GET /api/v1/restaurants?limit=20&offset=0
GET /api/v1/reviews?target_type=courier&target_id={courier_id}
```

Ответ со списком:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

Если сервис уже возвращает иной совместимый формат, он сохраняется до следующей версии API.

## Идемпотентность

Критичные команды принимают `Idempotency-Key`. Сейчас этот контракт реализован для резервирования платежа:

```http
POST /api/v1/payments/reservations
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

Повтор с тем же ключом должен вернуть ранее созданный результат или эквивалентное состояние без повторного side effect.

## WebSocket

Публичный tracking endpoint:

```text
ws://localhost:8000/ws/orders/{order_id}
```

Delivery Service принимает то же соединение на внутреннем порту:

```text
ws://localhost:8005/ws/orders/{order_id}
```

Соединение push-only: клиент держит WebSocket открытым, сервер отправляет события доставки.

Пример server-to-client сообщения:

```json
{
  "type": "location_update",
  "order_id": "2f7f05cf-4c1a-4b0d-81c9-b45b8dd86dd8",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "timestamp": "2026-05-31T12:34:56.789Z"
}
```

## Health и Metrics

Каждый сервис отдаёт:

```http
GET /health
GET /metrics
```

`/ready` добавляется только там, где readiness отличается от liveness. API Gateway уже предоставляет `/ready`.

## OpenAPI

FastAPI-сервисы публикуют `/docs` и `/openapi.json` для локальной диагностики контрактов.
