FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install application dependencies
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/api /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Create non-root user
RUN useradd -m maily
RUN chown -R maily:maily /app
USER maily

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Metadata
LABEL org.opencontainers.image.title="Maily API Service"
LABEL org.opencontainers.image.description="Main API service for Maily"
LABEL org.opencontainers.image.vendor="Maily Inc."
LABEL org.opencontainers.image.source="https://github.com/yourusername/maily"
LABEL org.opencontainers.image.version="1.0.0"