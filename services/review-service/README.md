# Review Service

Сервис отзывов и рейтингов. Хранит отзывы о ресторанах и курьерах, проверяет право на отзыв через Order и Delivery Service.

## Назначение

- Создание, чтение, обновление и удаление отзывов.
- Поддержка целей `restaurant` и `courier`.
- Проверка владения заказом.
- Проверка завершённой доставки перед созданием отзыва.
- Расчёт сводного рейтинга ресторана или курьера.
- Публикация события создания отзыва.

## API

### Health

- `GET /health`
- `GET /metrics`

### Reviews

- `POST /api/v1/reviews`
- `GET /api/v1/reviews`
- `GET /api/v1/reviews/{review_id}`
- `PATCH /api/v1/reviews/{review_id}`
- `DELETE /api/v1/reviews/{review_id}`
- `GET /api/v1/reviews/restaurants/{restaurant_id}/rating`
- `GET /api/v1/reviews/couriers/{courier_id}/rating`

## События Kafka

Публикует:
- `review-service.review.created`

## Валидация

Review Service использует прямые HTTP-вызовы:
- Order Service — проверка владения заказом и restaurant id;
- Delivery Service — статус доставки и courier id.

Цель отзыва хранится как `target_type + target_id`.

## Запуск

```bash
make up
curl http://localhost:8008/health
```

Локальный запуск только сервиса:

```bash
make dev-review
```

## Конфигурация

Настройки читаются из `services/review-service/src/config.py` с префиксом `REVIEW_SERVICE_`. Общие настройки PostgreSQL читаются через `POSTGRES_`, Kafka — через `KAFKA_`.

Ключевые группы:
- PostgreSQL database/user/password;
- Order Service URL;
- Delivery Service URL;
- Kafka enabled flag;
- metrics path.

## Миграции

```bash
cd services/review-service
alembic upgrade head
```

## Тестирование

```bash
make test-review
make test-review-unit
make test-review-integration
```

## Ограничения

- Courier identity приходит из Delivery Service contract, который сейчас использует mock-пул курьеров.
- Kafka publish best-effort до внедрения outbox.
