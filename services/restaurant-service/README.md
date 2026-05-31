# Restaurant Service

Сервис ресторанов и меню. Хранит каталог ресторанов, позиции меню и доступность позиций.

## Назначение

- Создание, обновление и деактивация ресторанов.
- Поиск ресторанов по фильтрам.
- CRUD позиций меню.
- Переключение доступности menu item.
- Валидация ресторанов и меню для Order Service.

## API

### Health

- `GET /health`
- `GET /metrics`

### Restaurants

- `POST /api/v1/restaurants`
- `GET /api/v1/restaurants`
- `GET /api/v1/restaurants/{restaurant_id}`
- `PUT /api/v1/restaurants/{restaurant_id}`
- `PATCH /api/v1/restaurants/{restaurant_id}`
- `DELETE /api/v1/restaurants/{restaurant_id}`
- `GET /api/v1/restaurants/{restaurant_id}/menu`

### Menu items

- `POST /api/v1/restaurants/{restaurant_id}/menu-items`
- `GET /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}`
- `PUT /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}`
- `PATCH /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}`
- `PATCH /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}/availability`
- `DELETE /api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}`

## События Kafka

При включённой публикации сервис отправляет текущие `event_type`:
- `restaurant.restaurant.created`
- `restaurant.restaurant.updated`
- `restaurant.restaurant.deactivated`
- `restaurant.menu_item.created`
- `restaurant.menu_item.updated`
- `restaurant.menu_item.availability_changed`
- `restaurant.menu_item.deleted`

## Хранилище

- PostgreSQL: `restaurants`, `menu_items`.
- Redis-параметры присутствуют в конфигурации, но каталог сейчас читается из PostgreSQL.

## Запуск

```bash
make up
curl http://localhost:8002/health
```

Локальный запуск только сервиса:

```bash
make dev-restaurant
```

## Конфигурация

Настройки читаются из `services/restaurant-service/src/config.py` с префиксом `RESTAURANT_SERVICE_`. Общие настройки Kafka читаются через `KAFKA_`, PostgreSQL — через `POSTGRES_`.

Ключевые группы:
- PostgreSQL database/user/password;
- API host/port/prefix;
- Kafka enabled flag;
- metrics path.

## Миграции

```bash
cd services/restaurant-service
alembic upgrade head
```

## Тестирование

```bash
make test-restaurant
make test-restaurant-unit
make test-restaurant-integration
```

## Ограничения

- Поиск реализован через фильтры PostgreSQL, без отдельного search engine.
- Публикация Kafka-событий best-effort до внедрения outbox.
- Именование restaurant events ещё не приведено к общему service-prefixed формату.
