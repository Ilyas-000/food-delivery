FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
COPY shared ./shared
COPY services/delivery-service/pyproject.toml ./services/delivery-service/
COPY services/delivery-service/README.md ./services/delivery-service/

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/delivery-service

FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 delivery

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=delivery:delivery shared /app/shared
COPY --chown=delivery:delivery services/delivery-service/src /app/services/delivery-service/src
COPY --chown=delivery:delivery services/delivery-service/alembic /app/services/delivery-service/alembic
COPY --chown=delivery:delivery services/delivery-service/alembic.ini /app/services/delivery-service/
COPY --chown=delivery:delivery services/delivery-service/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

USER delivery

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/shared/src

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
