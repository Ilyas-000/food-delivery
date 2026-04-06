FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
COPY shared ./shared
COPY services/notification-service/pyproject.toml ./services/notification-service/
COPY services/notification-service/README.md ./services/notification-service/

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/notification-service

FROM python:3.12-slim AS runtime

RUN useradd -m -u 1000 notification

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=notification:notification shared /app/shared
COPY --chown=notification:notification services/notification-service/src /app/services/notification-service/src

USER notification

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/shared/src

EXPOSE 8006

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

WORKDIR /app/services/notification-service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8006"]
