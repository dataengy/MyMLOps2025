FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY uv.lock* .

# Install dependencies
RUN uv sync --no-dev

# Copy source code
COPY src/ ./src/

# Create necessary directories
RUN mkdir -p data models dagster_home

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DAGSTER_HOME=/app/dagster_home

# Expose port
EXPOSE 3001

# Default command (will be overridden by docker-compose)
CMD ["uv", "run", "dagster", "dev", "--host", "0.0.0.0", "--port", "3001"]