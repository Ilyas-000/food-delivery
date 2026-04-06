FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
COPY shared ./shared
COPY services/analytics-service/pyproject.toml ./services/analytics-service/
COPY services/analytics-service/README.md ./services/analytics-service/

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/analytics-service

FROM python:3.12-slim AS runtime

RUN useradd -m -u 1000 analytics

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=analytics:analytics shared /app/shared
COPY --chown=analytics:analytics services/analytics-service/src /app/services/analytics-service/src

USER analytics

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/shared/src

EXPOSE 8007

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

WORKDIR /app/services/analytics-service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]
