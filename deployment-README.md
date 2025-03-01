# Maily Production Deployment Guide

This document provides an overview of the production deployment process for the Maily platform. The deployment infrastructure has been designed to be robust, secure, and scalable, with special attention to smooth deployments and easy recovery procedures.

## Deployment Components

Maily is deployed as a set of microservices in a Kubernetes cluster, with the following key components:

- **Frontend**: Next.js application deployed on Vercel
- **Backend Services**: Multiple FastAPI microservices deployed as containers
- **Database**: PostgreSQL database (Supabase)
- **Caching**: Redis for high-speed caching
- **Message Broker**: RabbitMQ for asynchronous processing
- **AI Layer**: OctoTools framework with adapters for OpenAI, Anthropic, and Google models
- **Blockchain Verification**: Smart contracts on Ethereum and Polygon
- **Monitoring**: Prometheus and Grafana
- **Security**: Vault for secrets management

## Getting Started

Before deploying, complete these prerequisite steps:

1. Review `deployment-checklist.md` to ensure all requirements are met
2. Copy `.env.production.template` to `.env.production` and fill in all values
3. Source your environment variables: `source .env.production`
4. Ensure you have appropriate access to cloud resources and Kubernetes cluster

## Deployment Scripts

The following scripts are available to facilitate the deployment process:

- **`scripts/validate-env-vars.sh`**: Validates that all required environment variables are set
- **`scripts/db-migration.sh`**: Handles database migrations with backup and restore capabilities
- **`scripts/deploy-ai-services.sh`**: Deploys AI-specific components and configurations
- **`scripts/master-deploy.sh`**: Main deployment script that orchestrates the entire process
- **`scripts/rollback.sh`**: Rolls back to a previous deployment state in case of issues

## Deployment Process

### Standard Deployment

For a standard production deployment:

```bash
# 1. Validate environment variables
./scripts/validate-env-vars.sh production

# 2. Deploy the entire platform
./scripts/master-deploy.sh production
```

The deployment will proceed through the following phases:
1. Environment validation
2. Infrastructure provisioning (Terraform)
3. Database migrations
4. Backend services deployment
5. Frontend deployment
6. AI services configuration
7. Monitoring setup
8. Verification tests
9. Traffic configuration

### Partial Deployments

For more targeted deployments, you can use flags with the master deployment script:

```bash
# Deploy only backend services
./scripts/master-deploy.sh production --skip-infrastructure --skip-database --skip-frontend --skip-ai

# Deploy only AI components
./scripts/master-deploy.sh production --skip-infrastructure --skip-database --skip-frontend --skip-backend
```

### Recovery Procedures

If a deployment fails, you can roll back to a previous known-good state:

```bash
# Roll back to a specific deployment
./scripts/rollback.sh production production-20250101-120000
```

## Deployment Architecture

The deployment follows a blue-green deployment strategy with the following characteristics:

- **Zero-downtime deployments**: Rolling updates ensure services remain available
- **Automated verification**: Smoke tests verify functionality post-deployment
- **Phased rollout**: Traffic is gradually shifted to new versions
- **Automatic scaling**: Services scale based on demand
- **Backup and recovery**: Database backups are created before migrations

## Monitoring and Alerting

After deployment, monitor the system health through:

- Grafana dashboards at `https://grafana.maily.io`
- Prometheus alerts configured for critical metrics
- Logging available in the ELK stack
- Regular health checks built into all services

## Security Considerations

The deployment process incorporates security best practices:

- All sensitive data is stored in Vault
- Services run with least-privilege principles
- Network policies restrict pod-to-pod communication
- All traffic is encrypted with TLS
- Container images are scanned for vulnerabilities before deployment

## Troubleshooting

Common deployment issues and their solutions:

- **Database migration failures**: Check `scripts/db-migration.sh` logs and restore from backup if needed
- **Pod scheduling failures**: Verify resource quotas and node capacity
- **AI service errors**: Check API keys and service connectivity
- **Frontend deployment failures**: Verify Vercel configuration and build logs

If you encounter persistent issues, consult the internal deployment troubleshooting guide.

## Maintenance Procedures

Regular maintenance tasks:

- Database backups run daily via Kubernetes CronJobs
- Certificate renewal is handled automatically by cert-manager
- Log rotation and cleanup is configured for all services
- Performance metrics are collected for optimization

## Contact

For deployment assistance, contact the DevOps team at devops@maily.io or through the #deployment-support Slack channel.
