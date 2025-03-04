# Production Deployment Guide

This guide provides a comprehensive overview of the Maily production deployment process.

## Deployment Architecture

Maily uses a modern, cloud-native architecture with the following components:

- **Frontend**: React/Next.js application deployed on Vercel
- **Backend Services**: Containerized microservices deployed on Kubernetes (AWS EKS)
- **Database**: PostgreSQL on AWS RDS
- **Caching**: Redis on AWS ElastiCache
- **Blockchain Integration**: Connection to Polygon for verification
- **Monitoring**: Prometheus, Grafana, and Datadog

## Deployment Tools

The following tools are required for deploying Maily:

- `kubectl` - For Kubernetes operations
- `jq` - For JSON processing in deployment scripts
- `vercel` - For frontend deployment
- PostgreSQL client tools for database migrations

## Deployment Scripts

Maily uses a unified deployment approach with the following scripts:

1. `/scripts/deploy-production.sh` - Main deployment script that supports:
   - `--migrate-only` - Run only database migrations
   - `--services-only` - Deploy only backend services
   - `--frontend-only` - Deploy only frontend

## Deployment Process

### 1. Pre-Deployment Checklist

Before deploying to production, ensure:

- All tests are passing in the CI pipeline
- Security scanning has been completed
- Required infrastructure is provisioned via Terraform
- Environment variables are configured in `config/.env.production`

### 2. Database Migrations

Database migrations are executed first to ensure schema compatibility:

```bash
./scripts/deploy-production.sh --migrate-only
```

After migrations complete, a verification period ensures database stability.

### 3. Backend Services Deployment

Backend services are deployed using a canary deployment strategy:

```bash
./scripts/deploy-production.sh --services-only
```

The deployment:
- Deploys Redis first as a dependency
- Uses canary deployment for the API service
- Deploys the AI service mesh
- Sets up monitoring infrastructure
- Includes a stabilization period

### 4. Frontend Deployment

The frontend is deployed to Vercel:

```bash
./scripts/deploy-production.sh --frontend-only
```

### 5. Monitoring and Verification

After deployment:
- Critical metrics are monitored (API response time, error rates, etc.)
- Blockchain verification rates are checked
- Service health endpoints are verified

## Rollback Procedure

If issues are detected post-deployment:

1. Assess the impact and determine if rollback is necessary
2. Execute the rollback script: `./scripts/rollback-production.sh`
3. Verify service stability after rollback

## Service URLs

- Frontend: https://maily.vercel.app
- API: https://api.maily.example.com
- Monitoring: https://monitor.maily.example.com

## Success Criteria

- All services meet 99.99% uptime SLA
- Response times under 200ms for 99% of requests
- System handles 10,000 concurrent users
- Recovery time objective (RTO) of 15 minutes
