FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY apps/ai-service/requirements-ai-mesh.txt .
RUN pip install --no-cache-dir -r requirements-ai-mesh.txt

# Copy application code
COPY apps/ai-service /app/

# Apply patches
RUN python -m patches.patch_aioredis

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/mesh/health || exit 1

# Run the application
CMD ["python", "main.py"]

# Metadata
LABEL org.opencontainers.image.title="Maily AI Service"
LABEL org.opencontainers.image.description="AI Mesh Network service for Maily"
LABEL org.opencontainers.image.vendor="Maily Inc."
LABEL org.opencontainers.image.source="https://github.com/yourusername/maily"
LABEL org.opencontainers.image.version="1.0.0"