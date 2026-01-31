# 🗺 Development Roadmap

> Пошаговый план разработки проекта Food Delivery с детальными задачами для каждой фазы.

## 📋 Принципы разработки

1. **Итеративная разработка** - каждая фаза завершается работающим сервисом
2. **Тестирование на каждом шаге** - пишем тесты параллельно с кодом
3. **Документирование решений** - фиксируем ADR (Architecture Decision Records)
4. **Обсуждение альтернатив** - перед реализацией обсуждаем варианты
5. **Постепенное усложнение** - от простого к сложному

## 🎯 Общая последовательность

```
Phase 0: Infrastructure Setup (1-2 дня)
    ↓
Phase 1: User Service + API Gateway (2-3 дня)
    ↓
Phase 2: Restaurant Service (2-3 дня)
    ↓
Phase 3: Order Service + Saga Pattern (4-5 дней) ← Самый сложный
    ↓
Phase 4: Payment Service (2-3 дня)
    ↓
Phase 5: Delivery Service + WebSocket (3-4 дня)
    ↓
Phase 6: Notification Service (2 дня)
    ↓
Phase 7: Analytics Service + ClickHouse (3 дня)
    ↓
Phase 8: Review Service (2 дня)
    ↓
Phase 9: Integration & Testing (3 дня)
    ↓
Phase 10: Monitoring & Observability (2-3 дня)
```

**Общее время:** ~4-5 недель

---

## Phase 0: Infrastructure Setup

**Цель:** Подготовить базовую инфраструктуру для разработки
**Продолжительность:** 1-2 дня
**Сложность:** ⭐⭐⭐

### Что делаем:
- Настраиваем Docker Compose с PostgreSQL, Redis, Kafka, ClickHouse
- Создаем структуру проекта (monorepo)
- Настраиваем shared код (общие утилиты, event модели)
- Создаем Makefile и скрипты для управления проектом

### Детальные задачи:

#### 0.1. Инициализация проекта

```bash
# Создать структуру
food-delivery/
├── services/          # Микросервисы
├── shared/            # Общий код
├── infrastructure/    # Docker Compose, конфиги
├── docs/              # Документация
├── scripts/           # Утилиты
└── tests/             # E2E тесты
```

**Чеклист:**
- [ ] Создать структуру каталогов
- [ ] Инициализировать Git
- [ ] Создать `.gitignore`
- [ ] Создать `README.md`
- [ ] Создать `AGENT-CONTEXT.md`
- [ ] Создать `DEVELOPMENT-ROADMAP.md`

#### 0.2. Docker Compose

**Файл:** `infrastructure/docker-compose.yml`

**Сервисы:**
- PostgreSQL 15 (с init script для создания БД)
- Redis 7
- Zookeeper + Kafka
- Kafka UI (для удобства)
- ClickHouse

**Чеклист:**
- [ ] Создать docker-compose.yml
- [ ] Создать init script для PostgreSQL (`init-databases.sh`)
- [ ] Создать script для Kafka топиков (`create-topics.sh`)
- [ ] Протестировать `make up`
- [ ] Проверить доступность всех сервисов

**Вопросы для обсуждения:**
- Нужен ли pgAdmin для управления PostgreSQL?
- Какие Kafka топики создать сразу?
- Нужна ли MongoDB для Event Store или пока пропускаем?

#### 0.3. Shared код

**Структура:**
```
shared/
├── events/            # Event модели (Pydantic)
│   ├── base.py
│   ├── order_events.py
│   └── payment_events.py
├── common/            # Утилиты
│   ├── kafka_client.py
│   ├── postgres_base.py
│   ├── redis_client.py
│   └── auth.py
└── proto/             # gRPC (опционально)
```

**Чеклист:**
- [ ] Создать `BaseEvent` модель
- [ ] Создать базовые event модели для Order и Payment
- [ ] Создать `KafkaProducer` wrapper
- [ ] Создать `KafkaConsumer` wrapper
- [ ] Создать базовые exceptions
- [ ] Создать JWT utilities

**Вопросы для обсуждения:**
- Версионирование событий - нужно сразу или потом?
- Outbox Pattern - реализовывать в shared или в каждом сервисе?

#### 0.4. Makefile и скрипты

**Чеклист:**
- [ ] Создать Makefile с командами (up, down, logs, health, etc.)
- [ ] Создать `scripts/check-health.sh`
- [ ] Создать `scripts/run-migrations.sh`
- [ ] Создать `.env.example`

**Критерии завершения Phase 0:**
- ✅ `make up` успешно запускает всю инфраструктуру
- ✅ Все БД созданы в PostgreSQL
- ✅ Kafka топики созданы
- ✅ Shared код структурирован и документирован

---

## Phase 1: User Service + API Gateway

**Цель:** Создать первый сервис с аутентификацией
**Продолжительность:** 2-3 дня
**Сложность:** ⭐⭐

### Зачем начинаем с User Service:
1. Простейшая логика (регистрация, логин, CRUD)
2. Освоение Clean Architecture на простом примере
3. JWT авторизация нужна для всех сервисов
4. Шаблон структуры для остальных сервисов

### Что реализуем:

#### User Service:
- Регистрация пользователя
- Логин (JWT)
- CRUD операции с профилем
- Роли: Customer, Courier, RestaurantOwner, Admin

#### API Gateway:
- Маршрутизация запросов
- JWT валидация
- Rate limiting
- CORS

### Структура User Service (Clean Architecture):

```
services/user-service/
├── src/
│   ├── domain/              # Бизнес-логика
│   │   ├── entities/        # User Entity
│   │   ├── value_objects/   # Email, UserRole
│   │   └── exceptions/      # Domain exceptions
│   │
│   ├── application/         # Use Cases
│   │   ├── use_cases/
│   │   │   ├── register_user.py
│   │   │   ├── login_user.py
│   │   │   └── get_user_profile.py
│   │   ├── dto/
│   │   └── interfaces/      # IUserRepository
│   │
│   ├── infrastructure/      # Внешние зависимости
│   │   ├── database/
│   │   │   ├── models.py    # SQLAlchemy
│   │   │   └── repositories/
│   │   └── security/        # Password hashing, JWT
│   │
│   ├── interface/           # API
│   │   └── api/
│   │       └── v1/
│   │           └── routes/
│   │
│   ├── config.py
│   └── main.py
│
└── tests/
```

### Детальные задачи:

**1.1. Domain Layer**
- [ ] User Entity с factory methods
- [ ] UserRole (Enum)
- [ ] Email Value Object
- [ ] Domain exceptions
- [ ] Unit тесты для Domain

**1.2. Application Layer**
- [ ] IUserRepository interface
- [ ] RegisterUserUseCase
- [ ] LoginUserUseCase
- [ ] GetUserProfileUseCase
- [ ] DTO модели
- [ ] Unit тесты для Use Cases

**1.3. Infrastructure Layer**
- [ ] SQLAlchemy модели
- [ ] UserRepository implementation
- [ ] Alembic миграции
- [ ] Password hashing (bcrypt)
- [ ] JWT handler
- [ ] Integration тесты

**1.4. Interface Layer**
- [ ] FastAPI routes (auth, users)
- [ ] Pydantic schemas (Request/Response)
- [ ] Dependencies (get_current_user)
- [ ] Exception handlers
- [ ] OpenAPI documentation
- [ ] Logout endpoint with refresh token revocation (Redis)
- [ ] JTI claim for refresh tokens
- [ ] Redis whitelist for active refresh tokens

**1.5. API Gateway**
- [ ] Создать api-gateway сервис
- [ ] Настроить маршрутизацию (proxy к User Service)
- [ ] JWT middleware
- [ ] Rate limiting
- [ ] Rate limiting on /login and /refresh
- [ ] CORS middleware

**Критерии завершения Phase 1:**
- ✅ Можно зарегистрироваться через API Gateway
- ✅ Можно залогиниться и получить JWT
- ✅ JWT токен работает для защищенных endpoints
- ✅ Все тесты проходят

---

## Phase 2: Restaurant Service

**Цель:** CRUD операции, работа с меню
**Продолжительность:** 2-3 дня
**Сложность:** ⭐⭐

### Что реализуем:
- Управление ресторанами
- Меню и блюда
- Категории блюд
- Доступность блюд (в наличии/нет)
- Часы работы ресторана

### Ключевые паттерны:
- Repository Pattern
- CQRS (базовый уровень - разделение команд/запросов)

### Детальные задачи:

**2.1. Domain Layer**
- [ ] Restaurant Entity
- [ ] MenuItem Entity
- [ ] Category Value Object
- [ ] Availability (enum: AVAILABLE, OUT_OF_STOCK)
- [ ] Domain events (MenuItemCreated, RestaurantUpdated)

**2.2. Application Layer**
- [ ] CreateRestaurantUseCase
- [ ] AddMenuItemUseCase
- [ ] UpdateMenuItemAvailabilityUseCase
- [ ] SearchRestaurantsUseCase (с фильтрами)

**2.3. Infrastructure**
- [ ] PostgreSQL models
- [ ] Repositories
- [ ] Миграции
- [ ] Redis caching для популярных ресторанов

**2.4. Interface**
- [ ] REST API endpoints
- [ ] Kafka producer (публикация событий)

**Критерии завершения Phase 2:**
- ✅ Можно создать ресторан и добавить меню
- ✅ Поиск ресторанов работает
- ✅ События публикуются в Kafka

---

## Phase 3: Order Service + Saga Pattern

**Цель:** Реализовать Saga для распределенных транзакций
**Продолжительность:** 4-5 дней
**Сложность:** ⭐⭐⭐⭐⭐

### Что реализуем:
- Создание заказа
- Saga Orchestrator
- Компенсирующие транзакции
- Статусы заказа (Created → Confirmed → Preparing → Ready → Delivering → Delivered)
- CQRS (Command/Query модели)
- Outbox Pattern

### Saga Flow:

```
1. Create Order (PENDING)
2. Validate Menu Items (Restaurant Service) ✅
3. Reserve Payment (Payment Service) ✅
4. Assign Courier (Delivery Service) ✅
5. Confirm Order (CONFIRMED)

При ошибке на любом шаге → Compensation
```

### Детальные задачи:

**3.1. Domain Layer**
- [ ] Order Aggregate (с вложенными entities)
- [ ] OrderItem Value Object
- [ ] OrderStatus (enum)
- [ ] Domain events (OrderCreated, OrderConfirmed, OrderCancelled)

**3.2. Application Layer - Saga Orchestrator**
- [ ] CreateOrderUseCase (Saga Orchestrator)
- [ ] SagaStep interface
- [ ] ValidateMenuItemsStep
- [ ] ReservePaymentStep
- [ ] AssignCourierStep
- [ ] Compensation logic

**3.3. CQRS**
- [ ] Command model (Order write)
- [ ] Query model (Order read - может быть денормализована)
- [ ] Проекция для read model

**3.4. Outbox Pattern**
- [ ] Outbox table
- [ ] Outbox publisher (фоновый процесс)

**3.5. Infrastructure**
- [ ] PostgreSQL models
- [ ] Repositories
- [ ] HTTP clients для других сервисов (с Circuit Breaker)
- [ ] Kafka producer/consumer

**Критерии завершения Phase 3:**
- ✅ Saga успешно создает заказ
- ✅ Компенсация работает при ошибках
- ✅ Outbox гарантирует доставку событий

---

## Phase 4: Payment Service

**Цель:** Обработка платежей
**Продолжительность:** 2-3 дня
**Сложность:** ⭐⭐⭐

### Что реализуем:
- Резервирование оплаты
- Подтверждение платежа
- Возврат средств (refund)
- История транзакций
- Идемпотентность

### Детальные задачи:

**4.1. Domain**
- [ ] Payment Entity
- [ ] PaymentStatus (enum: PENDING, COMPLETED, FAILED, REFUNDED)
- [ ] Money Value Object

**4.2. Application**
- [ ] ReservePaymentUseCase
- [ ] ConfirmPaymentUseCase
- [ ] RefundPaymentUseCase
- [ ] Idempotency key handling

**4.3. Infrastructure**
- [ ] Mock payment gateway (или Stripe sandbox)
- [ ] PostgreSQL models
- [ ] Kafka consumer (слушает OrderConfirmed)

**Критерии завершения Phase 4:**
- ✅ Saga в Order Service вызывает Payment Service
- ✅ Идемпотентность работает

---

## Phase 5: Delivery Service + WebSocket

**Цель:** Real-time трекинг курьера
**Продолжительность:** 3-4 дня
**Сложность:** ⭐⭐⭐⭐

### Что реализуем:
- Назначение курьера на заказ
- Обновление геопозиции курьера
- WebSocket для real-time обновлений клиентам
- Redis Pub/Sub для распределения обновлений

### Архитектура Real-time:

```
Courier App → POST /deliveries/location
    ↓
Delivery Service → Save to PostgreSQL
    ↓
Delivery Service → PUBLISH to Redis channel "delivery:{order_id}"
    ↓
WebSocket connections (subscribed to channel) → Push to clients
```

### Детальные задачи:

**5.1. Domain**
- [ ] Delivery Entity
- [ ] Courier Entity
- [ ] Location Value Object (lat, lon)
- [ ] DeliveryStatus

**5.2. Application**
- [ ] AssignCourierUseCase
- [ ] UpdateLocationUseCase
- [ ] CompleteDeliveryUseCase

**5.3. Infrastructure**
- [ ] PostgreSQL models
- [ ] Redis Pub/Sub client
- [ ] Kafka consumer

**5.4. Interface**
- [ ] REST API
- [ ] WebSocket endpoint (`/ws/orders/{order_id}`)
- [ ] Location update endpoint

**Критерии завершения Phase 5:**
- ✅ Курьер может обновлять геопозицию
- ✅ Клиенты получают обновления в real-time через WebSocket

---

## Phase 6: Notification Service

**Цель:** Уведомления по событиям
**Продолжительность:** 2 дня
**Сложность:** ⭐⭐

### Что реализуем:
- Email уведомления (mock SMTP)
- Push уведомления (mock)
- Шаблоны уведомлений
- Event-driven architecture

### Подписки на события:
- OrderCreated → Email клиенту
- OrderConfirmed → Email + Push
- CourierAssigned → Email + Push
- DeliveryCompleted → Email + Push

### Детальные задачи:

**6.1. Domain**
- [ ] Notification Entity
- [ ] NotificationType (EMAIL, PUSH, SMS)
- [ ] Template system

**6.2. Application**
- [ ] SendEmailUseCase
- [ ] SendPushUseCase

**6.3. Infrastructure**
- [ ] Mock SMTP client
- [ ] Mock Push client
- [ ] Kafka consumers (на все события)

**Критерии завершения Phase 6:**
- ✅ При создании заказа отправляется email

---

## Phase 7: Analytics Service + ClickHouse

**Цель:** Аналитика и метрики
**Продолжительность:** 3 дня
**Сложность:** ⭐⭐⭐

### Что реализуем:
- Агрегация данных из всех сервисов
- Запись в ClickHouse
- Dashboard API (топ блюд, статистика ресторанов)

### Метрики:
- Популярные блюда
- Выручка ресторанов
- Среднее время доставки
- Конверсия заказов

### Детальные задачи:

**7.1. Infrastructure**
- [ ] ClickHouse таблицы
- [ ] Kafka consumers (все события)
- [ ] ETL pipeline

**7.2. Application**
- [ ] GetTopDishesUseCase
- [ ] GetRestaurantStatsUseCase

**7.3. Interface**
- [ ] REST API для аналитики

**Критерии завершения Phase 7:**
- ✅ События пишутся в ClickHouse
- ✅ API возвращает статистику

---

## Phase 8: Review Service

**Цель:** Отзывы и рейтинги
**Продолжительность:** 2 дня
**Сложность:** ⭐⭐

### Что реализуем:
- Отзывы о ресторанах
- Отзывы о курьерах
- Рейтинговая система (1-5 звезд)

### Детальные задачи:

**8.1. Domain**
- [ ] Review Entity
- [ ] Rating Value Object

**8.2. Application**
- [ ] CreateReviewUseCase
- [ ] CalculateAverageRatingUseCase

**8.3. Infrastructure**
- [ ] PostgreSQL models

**Критерии завершения Phase 8:**
- ✅ Можно оставить отзыв после доставки

---

## Phase 9: Integration & Testing

**Цель:** E2E тесты всей системы
**Продолжительность:** 3 дня
**Сложность:** ⭐⭐⭐

### Что делаем:
- E2E тесты критичных сценариев
- Load testing (опционально)
- Исправление найденных багов

### E2E сценарии:

**9.1. Happy Path**
- [ ] Создание заказа → Оплата → Назначение курьера → Доставка

**9.2. Failure Scenarios**
- [ ] Отмена заказа при недоступности блюд
- [ ] Refund при ошибке оплаты
- [ ] Reassign курьера

**9.3. Load Testing**
- [ ] 100 concurrent orders
- [ ] Kafka consumer lag

**Критерии завершения Phase 9:**
- ✅ Все E2E тесты проходят
- ✅ Система stable под нагрузкой

---

## Phase 10: Monitoring & Observability

**Цель:** Метрики, логи, трейсинг
**Продолжительность:** 2-3 дня
**Сложность:** ⭐⭐⭐

### Что настраиваем:
- Prometheus + Grafana (метрики)
- Structured logging
- Distributed tracing (Jaeger - опционально)

### Метрики:
- Request rate, latency, errors
- Kafka lag
- Database connections

### Детальные задачи:

**10.1. Prometheus**
- [ ] Добавить prometheus_client в каждый сервис
- [ ] Метрики для HTTP endpoints
- [ ] Метрики для Kafka consumers

**10.2. Grafana**
- [ ] Dashboard для каждого сервиса
- [ ] Alerts на высокий error rate

**10.3. Logging**
- [ ] Structured logging (JSON)
- [ ] Correlation ID для трейсинга запросов

**Критерии завершения Phase 10:**
- ✅ Grafana dashboard работает
- ✅ Логи структурированы

---

## 🎯 Итоговый чеклист

- [ ] Phase 0: Infrastructure Setup
- [ ] Phase 1: User Service + API Gateway
- [ ] Phase 2: Restaurant Service
- [ ] Phase 3: Order Service + Saga Pattern
- [ ] Phase 4: Payment Service
- [ ] Phase 5: Delivery Service + WebSocket
- [ ] Phase 6: Notification Service
- [ ] Phase 7: Analytics Service + ClickHouse
- [ ] Phase 8: Review Service
- [ ] Phase 9: Integration & Testing
- [ ] Phase 10: Monitoring & Observability

**🎉 Проект готов!**
