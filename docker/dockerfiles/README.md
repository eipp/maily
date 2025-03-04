# Service Dockerfiles

This directory contains the Dockerfiles for each service in the Maily platform. Each service has its own subdirectory with a standardized structure.

## Service Directory Structure

Each service directory follows this structure:
- `Dockerfile` - The main Dockerfile for the service
- `docker-entrypoint.sh` - Entrypoint script for container initialization (if needed)
- `config/` - Service-specific configuration files for Docker environments
- `scripts/` - Any scripts needed for building or running the service in Docker

## Available Services

- `ai-service/` - AI Mesh Network service
- `api-service/` - Main API backend service
- `web/` - Web frontend application
- `analytics-service/` - Analytics processing service
- `email-service/` - Email delivery and processing service
- `workers/` - Background task workers