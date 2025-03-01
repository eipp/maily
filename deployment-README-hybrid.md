# Maily Hybrid Production Deployment Guide

This document provides an overview of the hybrid deployment strategy for the Maily platform, leveraging both serverless platforms and container orchestration to optimize the deployment process for Maily's unique architecture.

## Maily Architecture Overview

Maily consists of several key architectural layers:

- **Frontend Layer**: Next.js, React, Tailwind CSS, Canvas interface
- **Backend Layer**: Vercel Serverless Functions, Supabase, Redis, Temporal
- **AI & Data Layer**: Multiple AI models via Vercel AI SDK, OctoTools for agent orchestration, Vespa for vector search
- **Trust Infrastructure**: Blockchain integration, smart contracts, verification system

## Hybrid Deployment Approach

The deployment strategy uses the optimal hosting platform for each component:

### 1. Platform-Specific Deployments

| Component | Deployment Platform | Deployment Method |
|-----------|---------------------|-------------------|
| Frontend (Next.js) | Vercel | GitHub integration |
| API Functions | Vercel | GitHub integration |
| Database & Auth | Supabase | Supabase migrations |
| Vector Database | Managed Vespa | Kubernetes |
| Blockchain Components | AWS EKS | Kubernetes |
| Stateful Services | AWS EKS | Kubernetes |

### 2. Coordinated Deployment Process

The entire deployment is orchestrated through a unified GitHub Actions workflow (`.github/workflows/deploy-production.yml`) that coordinates deployments across all platforms while maintaining transactional integrity.

## Setup Requirements

### Vercel Configuration
- Vercel project set up with GitHub integration
- Environment variables configured in Vercel dashboard
- Authentication with Supabase configured

### Supabase Configuration
- Database instance provisioned
- Migration scripts ready
- Auth providers configured

### AWS/Kubernetes Configuration
- EKS cluster provisioned via Terraform
- IAM roles configured for GitHub Actions
- Namespace and resource quotas established
- Secrets management with AWS Secrets Manager

### CI/CD Configuration
- GitHub repository secrets configured (see below)
- Protected branches and environments established
- Approval workflows for production deployments

## Required Secrets

The following secrets need to be configured in your GitHub repository:

| Secret Name | Purpose |
|-------------|---------|
| `VERCEL_TOKEN` | Authentication for Vercel CLI |
| `VERCEL_ORG_ID` | Vercel organization identifier |
| `VERCEL_PROJECT_ID` | Vercel project identifier |
| `SUPABASE_DB_URL` | Supabase database connection string |
| `DATABASE_HOST` | Database hostname (for scripts) |
| `DATABASE_USER` | Database username |
| `DATABASE_PASSWORD` | Database password |
| `DATABASE_NAME` | Database name |
| `AWS_ACCESS_KEY_ID` | AWS authentication |
| `AWS_SECRET_ACCESS_KEY` | AWS authentication |
| `AWS_REGION` | Default AWS region |
| `EKS_CLUSTER_NAME` | Name of EKS cluster |
| `OPENAI_API_KEY` | OpenAI API access |
| `ANTHROPIC_API_KEY` | Anthropic API access |
| `GOOGLE_AI_API_KEY` | Google AI API access |
| `SLACK_WEBHOOK_URL` | Deployment notifications |

## Deployment Workflow

The deployment workflow follows these steps:

1. **Preparation**:
   - Validate environment variables
   - Generate unique deployment ID
   - Send deployment start notification

2. **Infrastructure**:
   - Apply Terraform configurations for AWS resources
   - Configure networking and security groups
   - Ensure EKS cluster is properly configured

3. **Database**:
   - Create database backup
   - Run Supabase migrations
   - Verify schema integrity

4. **Kubernetes Components**:
   - Build and push Docker images to GitHub Container Registry
   - Update Kubernetes manifests with new image tags
   - Apply deployments, services, and config maps
   - Verify deployments are running

5. **Frontend & API**:
   - Deploy Next.js frontend to Vercel
   - Deploy API functions to Vercel
   - Verify deployments are accessible

6. **Verification**:
   - Run smoke tests against all components
   - Verify integrations and cross-component communication
   - Collect and report test results

7. **Notification**:
   - Send deployment completion notification
   - Provide deployment summary and status

## Multi-Region Strategy

For global availability and performance, Maily uses a multi-region deployment:

- Frontend is deployed through Vercel's global edge network
- API functions are deployed to multiple Vercel regions
- Database uses Supabase's replication capabilities
- Kubernetes components are deployed to multiple AWS regions
- Cloudflare provides global load balancing and edge caching

## Deployment Scripts

The repository includes several scripts to facilitate deployments:

- **`scripts/validate-env-vars.sh`**: Validates that all required environment variables are set
- **`scripts/db-migration.sh`**: Handles database backups and schema migrations
- **`scripts/deploy-ai-services.sh`**: Configures AI providers and deploys specialized AI components
- **`scripts/master-deploy.sh`**: Orchestrates all deployment steps (used locally or for manual deployments)
- **`scripts/rollback.sh`**: Provides rollback capability in case of deployment issues
- **`scripts/smoke-test.js`**: Verifies system functionality after deployment

## GitOps with ArgoCD

For Kubernetes components, we implement GitOps principles using ArgoCD:

1. All Kubernetes manifests are stored in a Git repository
2. ArgoCD continuously synchronizes the desired state from Git to the cluster
3. Changes to the infrastructure are made through Git commits
4. ArgoCD handles rollbacks and drift detection

## Monitoring and Observability

The system uses a unified observability approach with:

- OpenTelemetry for metrics, traces, and logs collection
- Grafana dashboards for visualizing system performance
- Alertmanager for automated alerts
- Distributed tracing for cross-service request tracking
- Log aggregation with the ELK stack

## Rollback Procedures

In case of deployment issues:

1. For Vercel components:
   - Use Vercel dashboard to roll back to previous deployment
   - Or trigger rollback via Vercel API

2. For Supabase:
   - Restore database from the pre-deployment backup
   - Roll back migrations using Supabase CLI

3. For Kubernetes components:
   - Use `kubectl rollout undo` or ArgoCD to revert to previous state
   - Or run the `scripts/rollback.sh` script

## Security Considerations

The deployment process incorporates security best practices:

- All secrets managed through GitHub Actions secrets or external vault
- RBAC principles applied to all Kubernetes resources
- Network policies restricting pod-to-pod communication
- Encrypted communication with TLS throughout the stack
- Regular security scanning of container images and dependencies
- Compliance with GDPR and other relevant regulations

## Manual Deployment

For manual deployments when CI/CD is not suitable:

```bash
# 1. Validate environment variables
./scripts/validate-env-vars.sh production

# 2. Deploy using the master script
./scripts/master-deploy.sh production

# To deploy specific components:
./scripts/master-deploy.sh production --skip-frontend --skip-infra
```

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| Vercel deployment fails | Check build logs in Vercel dashboard, fix build errors, retry deployment |
| Database migration errors | Restore from backup using `pg_restore`, fix migration scripts, retry |
| Kubernetes pod failures | Check pod logs with `kubectl logs`, fix issues, redeploy |
| API connectivity issues | Verify network policies and security groups, check DNS resolution |
| AI service errors | Verify API keys and rate limits, check adapter configurations |

## Further Resources

- [Vercel Deployment Documentation](https://vercel.com/docs/concepts/deployments/overview)
- [Supabase Migration Guide](https://supabase.com/docs/guides/database/migrations)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [ArgoCD User Guide](https://argo-cd.readthedocs.io/en/stable/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
