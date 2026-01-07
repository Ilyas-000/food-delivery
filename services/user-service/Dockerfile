# Multi-stage Docker build для User Service
# Stage 1: Builder - устанавливаем зависимости
# Stage 2: Runtime - минимальный образ для запуска

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

# Metadata
LABEL maintainer="Food Delivery Team"
LABEL service="user-service"

# Устанавливаем системные зависимости для компиляции
# - build-essential: для компиляции Python пакетов с C-расширениями
# - libpq-dev: для asyncpg (PostgreSQL driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv (быстрый пакетный менеджер для Python)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только файлы с зависимостями (для кэширования слоя)
# Если зависимости не изменились, Docker переиспользует закэшированный слой
COPY services/user-service/pyproject.toml ./services/user-service/
COPY services/user-service/README.md ./services/user-service/
COPY shared ./shared

# Устанавливаем зависимости в виртуальное окружение
# uv venv создает .venv директорию
# ВАЖНО: сначала устанавливаем shared (так как user-service зависит от него)
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/user-service

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.12-slim AS runtime

# Устанавливаем только runtime зависимости (без компиляторов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем непривилегированного пользователя для безопасности
# Не запускаем приложение от root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем виртуальное окружение из builder stage
COPY --from=builder /app/.venv /app/.venv

# Копируем исходный код приложения
COPY services/user-service/src ./src

# Копируем shared код (нужен для editable install)
COPY shared /app/shared

# Меняем владельца файлов на appuser
RUN chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Добавляем .venv/bin в PATH
ENV PATH="/app/.venv/bin:$PATH"

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose порт (должен совпадать с api_port в config.py)
EXPOSE 8001

# Health check для Docker
# Проверяем /health endpoint каждые 30 секунд
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Запуск приложения через uvicorn
# --host 0.0.0.0: слушаем на всех интерфейсах (нужно для Docker)
# --port 8001: порт приложения
# --workers 1: в development один worker, в production можно увеличить
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
