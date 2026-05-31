# Order Service

Сервис заказов и saga-оркестрации. Создаёт заказ, валидирует меню, резервирует оплату и назначает доставку.

## Назначение

- Создание заказа.
- Синхронная saga-оркестрация.
- Компенсации при сбое после выполненных шагов.
- Чтение заказа по id.
- Публикация событий создания и подтверждения заказа.

## API

### Health

- `GET /health`
- `GET /metrics`

### Orders

- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`

Внешний доступ идёт через API Gateway. Внутренние saga-вызовы идут напрямую в Restaurant, Payment и Delivery Service.

## Saga flow

1. Создать заказ в локальном хранилище.
2. Опубликовать `order-service.order.created` best-effort.
3. Проверить restaurant/menu items через Restaurant Service.
4. Зарезервировать платёж через Payment Service.
5. Назначить курьера через Delivery Service.
6. Подтвердить заказ.
7. Опубликовать `order-service.order.confirmed` best-effort.

При ошибке выполняются компенсации уже завершённых шагов в обратном порядке.

## События Kafka

Публикует:
- `order-service.order.created`
- `order-service.order.confirmed`

## Хранилище

Repository backend выбирается настройкой:
- `memory` — лёгкий режим для локальных сценариев и unit-тестов;
- `postgres` — SQLAlchemy + Alembic.

## Запуск

```bash
make up
curl http://localhost:8003/health
```

Локальный запуск только сервиса:

```bash
make dev-order
```

## Конфигурация

Настройки читаются из `services/order-service/src/config.py` с префиксом `ORDER_SERVICE_`.

Ключевые группы:
- repository backend;
- saga backend (`mock` или `http`);
- saga step timeout;
- PostgreSQL database/user/password;
- downstream service URLs;
- Kafka enabled flag.

## Миграции

```bash
cd services/order-service
alembic upgrade head
```

## Тестирование

```bash
make test-order
make test-order-unit
make test-order-integration
```

## Ограничения

- `POST /api/v1/orders` держит HTTP-запрос открытым до завершения saga.
- Отдельное состояние saga-шагов не сохраняется.
- Kafka publish не атомарен с записью заказа до внедрения outbox.
