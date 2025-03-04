# Maily Configuration Guide

This document provides a comprehensive overview of configuration standards for the Maily platform across different technologies.

## Docker Configuration

### Standardized Practices

All Dockerfiles follow these best practices:

1. **Multi-stage builds** to reduce final image size
2. **Security hardening** including:
   - Non-root users for each service
   - Minimal base images
   - Reduced attack surface
3. **Build optimizations**:
   - Proper layer caching
   - Dependency installation separated from code changes
4. **Standardized naming** in docker/services directory

### Docker Compose

The unified docker-compose.yml file provides a complete local development environment with:
- API service
- Web front-end
- AI service
- Email service
- Background workers
- Postgres database
- Redis for caching and messaging

#### Usage

```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up api

# Rebuild services
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

For production deployment, refer to the Kubernetes manifests in the infrastructure directory.

## Next.js Configuration

### Consolidated Configuration

The Next.js configuration has been standardized with a single next.config.js file that supports:

1. ESM modules
2. Bundle analyzer (via environment variable)
3. Image optimization
4. Internationalization
5. Environment variable handling
6. Security headers

### Usage

Standard build:
```bash
npm run build:web
```

With bundle analyzer:
```bash
ANALYZE=true npm run build:web
```

### Key Features

- **Image Optimization**: Configured for WebP and AVIF formats
- **Internationalization**: Support for multiple languages
- **Security Headers**: CSP, CORS, and other security headers
- **Environment Variables**: Centralized handling of environment variables
- **Bundle Analysis**: On-demand bundle size analysis

## Python Requirements

### Requirements Structure

The project uses multiple requirements files to organize dependencies:

| File | Purpose |
|------|---------|
| `requirements.txt` | Base dependencies used across the project |
| `requirements-dev.txt` | Development-only dependencies |
| `apps/api/requirements.txt` | API-specific dependencies |
| `apps/api/requirements-ai-ml.txt` | AI and ML specific dependencies |
| `apps/workers/requirements.txt` | Worker-specific dependencies |
| `packages/config/monitoring/telemetry-requirements.txt` | Standardized OpenTelemetry packages |

### Installation Commands

For development:
```bash
pip install -r requirements-dev.txt
```

For API service:
```bash
pip install -r apps/api/requirements.txt
```

For AI/ML features:
```bash
pip install -r apps/api/requirements-ai-ml.txt
```

For workers:
```bash
pip install -r apps/workers/requirements.txt
```

### Standardized Libraries

#### HTTP Client

All services should use `httpx` for HTTP requests. Legacy clients (`requests`, `aiohttp`, `urllib3`) are maintained for backward compatibility but marked as deprecated.

```python
# Preferred way to make HTTP requests
import httpx

async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

#### Redis Client

All services should use the shared Redis client from `packages/database/src/redis/redis_client.py`. This provides standardized error handling, connection pooling, and circuit breaker functionality.

```python
from packages.database.src.redis.redis_client import get_redis_client

async def cache_data(key, value):
    redis = await get_redis_client()
    await redis.set(key, value, ex=3600)  # 1 hour expiration
```

#### OpenTelemetry

All services should use the standardized OpenTelemetry packages from `packages/config/monitoring/telemetry-requirements.txt`. This ensures consistent versioning across all services.

### Dependency Management Guidelines

1. Add the dependency to the appropriate requirements file
2. Use pinned versions (e.g., `package==1.2.3`)
3. Organize the dependency under the appropriate category
4. Run tests to ensure compatibility
5. For OpenTelemetry packages, always use the centralized file