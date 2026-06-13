# Use a multi-stage build to keep the final image small
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv
RUN uv sync --frozen --no-dev --no-install-project

# Final stage
FROM python:3.14-slim-bookworm

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY main.py ./
COPY data/ ./data/

# Place the virtual environment's binaries on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run expects the app to listen on the port defined by $PORT (defaults to 8080)
ENV PORT=8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
