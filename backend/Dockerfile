# Stage 1: Build dependencies with uv
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Stage 2: Production image
FROM python:3.13-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY scripts ./scripts
COPY data ./data

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations, seed problems, and start server
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed_problems.py seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
