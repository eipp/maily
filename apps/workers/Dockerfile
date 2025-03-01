# Maily Workers Dockerfile
# Standardized for production use

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 maily && \
    adduser --system --uid 1001 --gid 1001 maily && \
    chown -R maily:maily /app

# Switch to non-root user
USER maily

# Command to run the worker
CMD ["python", "-m", "workers.email_worker"]
