FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock
COPY services/payment-service/pyproject.toml ./services/payment-service/
COPY services/payment-service/README.md ./services/payment-service/
COPY shared ./shared

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/payment-service

FROM python:3.12-slim AS runtime

RUN useradd -m -u 1000 payment

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=payment:payment services/payment-service/src /app/services/payment-service/src
COPY --chown=payment:payment shared /app/shared

USER payment

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

WORKDIR /app/services/payment-service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]
