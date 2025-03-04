# Docker Configuration

This directory contains all Docker-related configuration files for the Maily platform.

## Structure

- `dockerfiles/` - Standardized Dockerfiles for all services (preferred)
- `services/` - Legacy service-specific Dockerfiles (being consolidated)
  - `ai-service/` - AI service Dockerfile and related files
  - `api-service/` - API service Dockerfile and related files
  - `web/` - Web application Dockerfile and related files
  - `workers/` - Worker service Dockerfiles
- `init-scripts/` - Database and service initialization scripts
- `test-init-scripts/` - Test environment initialization scripts

## Usage

The standardized Dockerfiles in the `dockerfiles/` directory should be used for building services:

```bash
docker build -t maily/service-name -f docker/dockerfiles/service-name.Dockerfile .
```

The main docker-compose files in the repository root reference these Dockerfiles.

## Best Practices

- Keep Dockerfiles minimal and efficient
- Use multi-stage builds to reduce image size
- Share common base images where appropriate
- Include proper healthchecks
- Follow security best practices for containerization

## Standardization

As part of the repository organization improvements, the following changes have been made:

1. Dockerfiles are being consolidated in the `dockerfiles/` directory
2. Common patterns are standardized across services
3. Legacy service-specific Dockerfiles will be gradually deprecated

## Migration

- All new services should create their Dockerfile in the `dockerfiles/` directory
- Existing services should gradually migrate their Dockerfiles from `services/` to `dockerfiles/`
- CI/CD pipelines should be updated to use the new Dockerfile locations