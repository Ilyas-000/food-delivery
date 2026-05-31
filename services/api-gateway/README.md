# API Gateway

Единая внешняя точка входа в Food Delivery Platform. Gateway валидирует JWT, применяет rate limiting и circuit breaker, проксирует REST и WebSocket запросы в доменные сервисы.

## Назначение

- Проксирование публичных `/api/v1/*` маршрутов в сервисы.
- Проверка JWT для защищённых маршрутов.
- Rate limiting auth-flow и глобальных auth-запросов через Redis.
- Circuit breaker для downstream-сервисов.
- Проброс `X-Request-ID` и `X-Correlation-ID`.
- WebSocket proxy для delivery tracking.

## Маршруты

### Health

- `GET /health`
- `GET /ready`
- `GET /metrics`

### REST proxy

| Префикс | Downstream |
|---|---|
| `/api/v1/auth/*` | User Service |
| `/api/v1/users/*` | User Service |
| `/api/v1/restaurants/*` | Restaurant Service |
| `/api/v1/orders/*` | Order Service |
| `/api/v1/payments/*` | Payment Service |
| `/api/v1/deliveries/*` | Delivery Service |
| `/api/v1/analytics/*` | Analytics Service |
| `/api/v1/reviews/*` | Review Service |

### WebSocket proxy

- `GET /ws/orders/{order_id}` -> Delivery Service

## Запуск

```bash
make up
curl http://localhost:8000/health
```

Локальный запуск только gateway:

```bash
make dev-gateway
```

## Конфигурация

Настройки читаются из `services/api-gateway/src/config.py` с префиксом `GATEWAY_`.

Ключевые группы:
- JWT secret и algorithm;
- Redis host/port/db для rate limiting;
- URL downstream-сервисов;
- proxy timeouts;
- circuit breaker thresholds;
- auth rate limits;
- structured logging.

Docker Compose задаёт значения для локальной сети сервисов в `infrastructure/docker-compose.yml`.

## Тестирование

```bash
make test-gateway
make test-gateway-unit
make test-gateway-integration
```

## Ограничения

- Circuit breaker хранит состояние в процессе.
- Endpoint-specific rate limits покрывают не все доменные маршруты.
- Retry policy для transient downstream errors требует отдельной настройки.
