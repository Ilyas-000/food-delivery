# Payment Service

Сервис жизненного цикла платежей. Предоставляет контракт резервирования средств для Order Service и публичные операции чтения/подтверждения/возврата.

## Назначение

- Резервирование средств для заказа.
- Освобождение резерва как saga-компенсация.
- Подтверждение платежа.
- Возврат платежа.
- История платежей.
- Идемпотентность резервирования через `Idempotency-Key`.

## API

### Health

- `GET /health`
- `GET /metrics`

### Payments

- `POST /api/v1/payments/reservations`
- `DELETE /api/v1/payments/reservations/{reservation_id}`
- `GET /api/v1/payments/history`
- `GET /api/v1/payments/{payment_id}`
- `POST /api/v1/payments/{payment_id}/confirm`
- `POST /api/v1/payments/{payment_id}/refund`

## Запуск

```bash
make up
curl http://localhost:8004/health
```

Локальный запуск только сервиса:

```bash
make dev-payment
```

## Конфигурация

Настройки читаются из `services/payment-service/src/config.py` с префиксом `PAYMENT_SERVICE_`.

Ключевые группы:
- API host/port/prefix;
- metrics path;
- environment/debug flags.

## Тестирование

```bash
make test-payment
make test-payment-unit
make test-payment-integration
```

## Ограничения

- Хранилище in-memory.
- Kafka-события платежей описаны в topic bootstrap, но сервис сейчас не публикует их.
