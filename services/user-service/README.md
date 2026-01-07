# User Service

**Сервис управления пользователями и аутентификации**

## Описание

User Service отвечает за:
- Регистрацию новых пользователей
- Аутентификацию (JWT токены)
- Управление профилями пользователей
- Управление ролями (Customer, Courier, RestaurantOwner, Admin)

## Технологии

- **FastAPI** - веб-фреймворк
- **SQLAlchemy 2.0** - ORM (async)
- **Alembic** - миграции БД
- **PostgreSQL** - база данных
- **Redis** - кэш и сессии
- **JWT** - аутентификация
- **Bcrypt** - хеширование паролей

## Структура проекта (Clean Architecture)

```
src/
├── domain/              # Бизнес-логика (независимая от фреймворков)
│   ├── entities/        # Сущности (User)
│   ├── value_objects/   # Value Objects (Email, UserRole)
│   └── exceptions/      # Domain исключения
│
├── application/         # Use Cases (бизнес-правила приложения)
│   ├── use_cases/       # Use Cases (RegisterUser, LoginUser)
│   ├── dto/             # Data Transfer Objects
│   └── interfaces/      # Интерфейсы (IUserRepository)
│
├── infrastructure/      # Внешние зависимости
│   ├── database/        # PostgreSQL (SQLAlchemy)
│   └── security/        # JWT, password hashing
│
└── interface/           # Внешний интерфейс (API)
    └── api/v1/routes/   # FastAPI routes
```

## Зависимости между слоями

```
Interface → Application → Domain
    ↓           ↓
Infrastructure
```

**Правила:**
- Domain не знает о других слоях (чистая бизнес-логика)
- Application использует Domain и определяет интерфейсы
- Infrastructure реализует интерфейсы из Application
- Interface использует Application

## Локальная разработка

### Запуск через Docker Compose (рекомендуется)

```bash
# Из корня проекта
cd infrastructure
docker-compose up user-service

# Проверка health check
curl http://localhost:8001/health

# API документация
open http://localhost:8001/docs
```

### Запуск локально (для разработки)

```bash
# Установка зависимостей
cd services/user-service
uv venv
source .venv/bin/activate  # или .venv\Scripts\activate на Windows
uv pip install -e .
uv pip install -e ../../shared

# Запуск PostgreSQL и Redis через Docker
cd ../../infrastructure
docker-compose up postgres redis

# Запуск сервиса
cd ../services/user-service
python -m src.main

# Или через uvicorn с hot-reload
uvicorn src.main:app --reload --port 8001
```

## Переменные окружения

Все переменные используют prefix `USER_SERVICE_`:

```bash
# Service
USER_SERVICE_SERVICE_NAME=user-service
USER_SERVICE_ENVIRONMENT=development
USER_SERVICE_DEBUG=true
USER_SERVICE_LOG_LEVEL=INFO

# API
USER_SERVICE_API_HOST=0.0.0.0
USER_SERVICE_API_PORT=8001

# Database
USER_SERVICE_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/user_service

# JWT
USER_SERVICE_JWT_SECRET_KEY=your-secret-key
USER_SERVICE_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
USER_SERVICE_JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
USER_SERVICE_REDIS_HOST=localhost
USER_SERVICE_REDIS_PORT=6379
```

## API Endpoints

### Health Checks

- `GET /health` - простая проверка доступности
- `GET /ready` - проверка готовности с зависимостями

### Authentication (TODO)

- `POST /api/v1/auth/register` - регистрация
- `POST /api/v1/auth/login` - логин
- `POST /api/v1/auth/refresh` - обновление токена
- `POST /api/v1/auth/logout` - выход

### Users (TODO)

- `GET /api/v1/users/me` - текущий пользователь
- `PATCH /api/v1/users/me` - обновить профиль
- `GET /api/v1/users/{user_id}` - получить пользователя (admin)

## Тестирование

```bash
# Unit тесты
pytest tests/unit

# Integration тесты
pytest tests/integration

# Все тесты с coverage
pytest --cov=src tests/

# Только быстрые тесты
pytest -m "not slow"
```

## Миграции базы данных

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# История миграций
alembic history
```

## Разработка

### Добавление новой фичи

1. **Domain Layer**: создать entities, value objects
2. **Application Layer**: создать use case, DTO, interface
3. **Infrastructure Layer**: реализовать interface (repository, external service)
4. **Interface Layer**: добавить API endpoint
5. **Tests**: написать unit и integration тесты

### Code Style

```bash
# Форматирование
ruff format .

# Линтинг
ruff check .

# Type checking
mypy src/
```

## TODO (следующие ветки)

- [ ] Реализация регистрации пользователей
- [ ] Реализация аутентификации (JWT)
- [ ] CRUD операции с профилем
- [ ] Unit и integration тесты
- [ ] Kafka события (UserCreated, UserUpdated)
- [ ] Redis кэширование
