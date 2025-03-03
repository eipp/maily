# Docker Configuration

This directory contains all Docker-related configuration files for the Maily platform.

## Structure

- `services/` - Dockerfiles for each service
  - `ai-service/` - AI service Dockerfile and related files
  - `api-service/` - API service Dockerfile and related files
  - `web/` - Web application Dockerfile and related files
  - `workers/` - Worker service Dockerfiles
- `init-scripts/` - Database and service initialization scripts
- `test-init-scripts/` - Test environment initialization scripts

## Usage

Each service directory contains a complete Dockerfile and any necessary configuration files for building and running that service. The main docker-compose files in the repository root reference these Dockerfiles.

## Best Practices

- Keep Dockerfiles minimal and efficient
- Use multi-stage builds to reduce image size
- Share common base images where appropriate
- Include proper healthchecks
- Follow security best practices for containerization