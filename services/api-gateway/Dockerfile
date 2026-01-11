# Multi-stage Docker build for API Gateway

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy workspace files for dependency resolution
COPY pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock

# Copy service metadata for caching
COPY services/api-gateway/pyproject.toml ./services/api-gateway/
COPY services/api-gateway/README.md ./services/api-gateway/
COPY shared ./shared

# Install dependencies in a virtual environment
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e /app/shared && \
    uv pip install -e /app/services/api-gateway

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.12-slim AS runtime

# Create non-root user
RUN useradd -m -u 1000 gateway

WORKDIR /app

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Copy application code with correct ownership for the non-root runtime user
COPY --chown=gateway:gateway services/api-gateway/src /app/services/api-gateway/src
COPY --chown=gateway:gateway shared /app/shared

# Switch to non-root user
USER gateway

# Use venv python
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)"

# Run application
WORKDIR /app/services/api-gateway
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
