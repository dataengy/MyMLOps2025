FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install MLflow and dependencies
RUN pip install \
    mlflow>=2.8.0 \
    psycopg2-binary>=2.9.0 \
    boto3>=1.34.0

# Create directories
RUN mkdir -p /mlflow/artifacts

# Expose port
EXPOSE 5000

# Default command (will be overridden by docker-compose)
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]