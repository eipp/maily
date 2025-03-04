# Maily Python Requirements

This document outlines the Python requirements structure for the Maily project.

## Requirements Files

The project uses multiple requirements files to organize dependencies:

| File | Purpose |
|------|---------|
| `requirements.txt` | Base dependencies used across the project |
| `requirements-dev.txt` | Development-only dependencies |
| `apps/api/requirements.txt` | API-specific dependencies |
| `apps/api/requirements-ai-ml.txt` | AI and ML specific dependencies |
| `apps/workers/requirements.txt` | Worker-specific dependencies |
| `packages/config/monitoring/telemetry-requirements.txt` | Standardized OpenTelemetry packages |

## Installation

### For Development

```bash
pip install -r requirements-dev.txt
```

### For API Service

```bash
pip install -r apps/api/requirements.txt
```

### For AI/ML Features

```bash
pip install -r apps/api/requirements-ai-ml.txt
```

### For Workers

```bash
pip install -r apps/workers/requirements.txt
```

## Standard Libraries

### HTTP Client

All services should use `httpx` for HTTP requests. Legacy clients (`requests`, `aiohttp`, `urllib3`) are maintained for backward compatibility but marked as deprecated.

### OpenTelemetry

All services should use the standardized OpenTelemetry packages from `packages/config/monitoring/telemetry-requirements.txt`. This ensures consistent versioning across all services.

### Redis Client

All services should use the shared Redis client from `packages/database/src/redis/redis_client.py`. This provides standardized error handling, connection pooling, and circuit breaker functionality.

## Dependency Management

We use pinned versions for all dependencies to ensure reproducibility. When adding new dependencies, please follow these guidelines:

1. Add the dependency to the appropriate requirements file
2. Use pinned versions (e.g., `package==1.2.3`)
3. Organize the dependency under the appropriate category
4. Run tests to ensure compatibility
5. For OpenTelemetry packages, always use the centralized file

## Removing Redundancies

When cleaning up requirements:

1. Don't include built-in Python modules (e.g., `asyncio`)
2. Don't duplicate dependencies across multiple requirements files (use `-r` to include a base file)
3. Use consistent versions across related packages (e.g., all OpenTelemetry components)
4. Add deprecation comments for libraries being phased out