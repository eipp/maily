# Maily Infrastructure

This directory contains infrastructure-related configurations and resources for the Maily platform.

## Docker Configuration

The Docker configuration for Maily has been standardized to follow best practices:

- **Standardized Dockerfiles**: All service Dockerfiles have been moved to their respective application directories:
  - API: `apps/api/Dockerfile`
  - Web: `apps/web/Dockerfile`
  - Workers: `apps/workers/Dockerfile`

- **Docker Compose**: The root `docker-compose.yml` file has been updated to use the standardized Dockerfiles.

- **Documentation**: Comprehensive documentation about the Docker setup can be found in the root `DOCKER.md` file.

## Infrastructure Components

The Maily platform consists of the following infrastructure components:

### Core Services

- **API Service**: FastAPI-based backend service
- **Web Application**: Next.js-based frontend application
- **Workers**: Background processing services

### Supporting Services

- **Database**: PostgreSQL database for persistent storage
- **Redis**: In-memory data store for caching and message queuing

## Local Development

For local development, you can use Docker Compose:

```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up api web

# Build and start services
docker-compose up --build
```

## Production Deployment

For production deployment, refer to the deployment documentation in the root directory.

## Infrastructure as Code

Infrastructure as Code (IaC) configurations for cloud deployments are maintained in this directory:

- **AWS**: AWS CloudFormation templates and scripts
- **Azure**: Azure Resource Manager templates
- **GCP**: Google Cloud Deployment Manager configurations

## Monitoring and Logging

Monitoring and logging configurations are also maintained in this directory:

- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **ELK Stack**: Logging infrastructure

## Security

Security-related configurations and documentation:

- **Network Policies**: Network security configurations
- **Secret Management**: Guidelines for managing secrets
- **Compliance**: Compliance-related documentation

## Backup and Recovery

Backup and recovery procedures and configurations:

- **Database Backups**: Database backup configurations
- **Disaster Recovery**: Disaster recovery procedures

## Maintenance

Maintenance procedures and scripts:

- **Database Migrations**: Database migration procedures
- **Service Updates**: Service update procedures
- **Rollback Procedures**: Procedures for rolling back deployments
