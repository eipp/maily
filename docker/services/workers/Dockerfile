FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY apps/workers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/workers /app/

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
  CMD curl -f http://localhost:8082/health || exit 1

# Run the application
CMD ["python", "email_worker.py"]

# Metadata
LABEL org.opencontainers.image.title="Maily Workers"
LABEL org.opencontainers.image.description="Background workers for Maily"
LABEL org.opencontainers.image.vendor="Maily Inc."
LABEL org.opencontainers.image.source="https://github.com/yourusername/maily"
LABEL org.opencontainers.image.version="1.0.0"