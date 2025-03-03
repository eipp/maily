# Maily DevOps Setup

This document provides an overview of the DevOps setup for Maily, an AI-driven email marketing platform. It includes information about the DevOps strategy, infrastructure setup, monitoring, and automation.

## Overview

Maily's DevOps infrastructure is designed to support a complex, distributed system with the following components:

- Next.js frontend
- Vercel serverless functions
- AI services
- Real-time Canvas collaboration feature with WebSocket management
- Blockchain integration for trust infrastructure and smart contracts

## DevOps Strategy

The DevOps strategy for Maily is documented in `devops-strategy.md`. This document outlines the approach to managing the entire DevOps lifecycle, including:

- Infrastructure architecture
- CI/CD pipeline
- Monitoring and observability
- Security
- Scalability
- Disaster recovery
- Automation
- Developer experience
- Implementation plan
- Maintenance and support

## Infrastructure Setup

The infrastructure setup is automated using the `scripts/setup-devops-infrastructure.sh` script. This script sets up the following components:

- AWS credentials configuration
- Terraform backend setup
- EKS cluster setup
- Kubernetes namespaces setup
- Vault setup for secrets management
- Monitoring setup
- CI/CD setup
- Docker registry setup
- Vercel setup
- WebSocket infrastructure setup
- Blockchain infrastructure setup

### Usage

```bash
# Make the script executable
chmod +x scripts/setup-devops-infrastructure.sh

# Run the script
./scripts/setup-devops-infrastructure.sh
```

## Monitoring Setup

Monitoring is a critical component of the DevOps infrastructure. Maily uses Datadog for comprehensive monitoring of all services, with special focus on AI services, WebSocket collaboration, and blockchain components.

The monitoring setup is automated using the `scripts/setup-datadog-monitoring.sh` script. This script sets up the following components:

- Datadog API key configuration
- Datadog RUM configuration
- Kubernetes namespace creation
- Kubernetes secrets creation
- Kubernetes ConfigMaps creation
- Datadog Helm chart installation
- Datadog dashboards creation
- Datadog monitors creation

### Usage

```bash
# Make the script executable
chmod +x scripts/setup-datadog-monitoring.sh

# Set the Datadog API key
export DATADOG_API_KEY=your_api_key

# Set the Datadog APP key (optional, for dashboard and monitor creation)
export DATADOG_APP_KEY=your_app_key

# Set the Datadog RUM configuration (optional, for Real User Monitoring)
export DATADOG_RUM_APP_ID=your_rum_app_id
export DATADOG_RUM_CLIENT_TOKEN=your_rum_client_token

# Run the script
./scripts/setup-datadog-monitoring.sh
```

## CI/CD Pipeline

The CI/CD pipeline is implemented using GitHub Actions. The workflow is defined in `.github/workflows/unified-ci-cd.yml`. The pipeline includes the following stages:

1. Lint and Type Check
2. Testing
3. Security Scanning
4. Build
5. Deployment to Staging
6. Deployment to Production

## Deployment

Deployment is automated using the `mailylaunch.sh` script. This script is referenced in the CI/CD pipeline and can also be used for manual deployments.

### Usage

```bash
# Deploy to staging
./mailylaunch.sh deploy --env=staging

# Deploy to production
./mailylaunch.sh deploy --env=production
```

## Security

Security is a critical aspect of the DevOps infrastructure. The following security measures are implemented:

- Vault for secrets management
- TLS for all services and communications
- Network policies for service-to-service communication control
- RBAC for Kubernetes access control
- WAF for web application protection
- Automated security scanning in the CI/CD pipeline

## Scalability

The infrastructure is designed to be scalable to accommodate growing workloads. The following scalability measures are implemented:

- Horizontal scaling for stateless services
- Vertical scaling for database and cache services
- Auto scaling based on CPU, memory, and custom metrics
- Load balancing for distributing traffic

## Disaster Recovery

Disaster recovery procedures are implemented to ensure business continuity in case of failures. The following disaster recovery measures are implemented:

- Database backups with point-in-time recovery
- S3 backups for file storage
- Configuration backups for infrastructure and application configurations
- Automated and manual failover procedures
- Regular testing of recovery procedures

## Maintenance

Regular maintenance procedures are implemented to ensure the health and performance of the infrastructure. The following maintenance tasks are automated:

- Security updates for all components
- Dependency updates
- Performance monitoring and optimization
- Capacity planning and scaling

## Support

For support with the DevOps infrastructure, please contact:

- DevOps team: devops@justmaily.com
- Technical lead: tech-lead@justmaily.com
