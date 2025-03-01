# Docker Configuration Directory

## Important Notice: Dockerfiles Have Been Standardized

**The Dockerfiles previously located in this directory have been standardized and moved to their respective application directories.**

Please refer to the following locations for the current Dockerfiles:

- API Service: `apps/api/Dockerfile`
- Web Application: `apps/web/Dockerfile`
- Workers: `apps/workers/Dockerfile`

## Docker Compose

The root `docker-compose.yml` file has been updated to use the standardized Dockerfiles.

## Documentation

Comprehensive documentation about the Docker setup can be found in the root `DOCKER.md` file.

## Purpose of This Directory

This directory now serves as a location for:

1. Docker-related utilities and helper scripts
2. Custom Docker images that don't belong to a specific application
3. Docker Compose overrides for specific environments
4. Docker-related configuration files

## Docker Utilities

The following utilities are available in this directory:

- **docker-compose.dev.yml**: Development-specific Docker Compose overrides
- **docker-compose.test.yml**: Testing-specific Docker Compose overrides
- **docker-compose.prod.yml**: Production-specific Docker Compose overrides

## Usage

To use the environment-specific Docker Compose files:

```bash
# Development environment
docker-compose -f docker-compose.yml -f infrastructure/docker/docker-compose.dev.yml up

# Testing environment
docker-compose -f docker-compose.yml -f infrastructure/docker/docker-compose.test.yml up

# Production environment
docker-compose -f docker-compose.yml -f infrastructure/docker/docker-compose.prod.yml up
```
