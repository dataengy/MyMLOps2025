FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install monitoring dependencies
RUN pip install \
    evidently>=0.4.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0

# Copy monitoring scripts
COPY src/monitoring/ ./monitoring/

# Create directories
RUN mkdir -p reports data models

# Expose port
EXPOSE 8001

# Start monitoring service
CMD ["python", "-m", "http.server", "8001"]