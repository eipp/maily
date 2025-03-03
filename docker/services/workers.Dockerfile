# Multi-stage build for Workers Service
FROM python:3.12-slim AS build

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY apps/workers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy only necessary files from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code
COPY apps/workers /app

# Set environment variables
ENV PYTHONPATH=/app

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Command to run the application
CMD ["python", "email_worker.py"]
