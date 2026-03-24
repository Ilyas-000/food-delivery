FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
COPY services/delivery-service/pyproject.toml ./services/delivery-service/
COPY services/delivery-service/README.md ./services/delivery-service/

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/services/delivery-service

FROM python:3.12-slim AS runtime

RUN useradd -m -u 1000 delivery

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=delivery:delivery services/delivery-service/src /app/services/delivery-service/src

USER delivery

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

WORKDIR /app/services/delivery-service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]
