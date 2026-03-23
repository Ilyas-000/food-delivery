# Multi-stage Docker build for Order Service

FROM python:3.12-slim AS builder

LABEL maintainer="Food Delivery Team"
LABEL service="order-service"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
COPY services/order-service/pyproject.toml ./services/order-service/
COPY services/order-service/README.md ./services/order-service/
COPY shared ./shared

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/order-service

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY services/order-service/src ./services/order-service/src
COPY services/order-service/alembic ./services/order-service/alembic
COPY services/order-service/alembic.ini ./services/order-service/
COPY shared /app/shared
COPY services/order-service/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chown -R appuser:appuser /app && \
    chmod +x /app/docker-entrypoint.sh

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
