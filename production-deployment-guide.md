# Maily Production Deployment Guide

This guide provides step-by-step instructions for deploying Maily to production using our hybrid deployment architecture.

## Deployment Architecture Overview

Maily uses a hybrid deployment strategy that optimizes each component:

- **Frontend (Next.js)**: Deployed to Vercel's global edge network
- **API Functions**: Deployed as Vercel serverless functions
- **Database & Auth**: Managed by Supabase
- **AI Services**: Deployed as services with multi-provider adapters
- **Stateful Services**: Deployed to Kubernetes (Redis, RabbitMQ, etc.)
- **Blockchain Components**: Deployed to Kubernetes

## Prerequisites

Before you begin, ensure you have:

1. Completed all items in the [deployment checklist](./deployment-checklist.md)
2. Set up all required environment variables in `.env.production`
3. Required access to all services (Vercel, Supabase, etc.)
4. Access to the DNS configuration for your domain

## Deployment Options

You have three deployment options:

1. **GitHub Actions (Recommended)**: Fully automated deployment triggered by commits or manual runs
2. **Local Scripted Deployment**: Using our deployment scripts from your machine
3. **Manual Deployment**: Step-by-step manual deployment process

## Option 1: GitHub Actions Deployment

The simplest way to deploy is using our GitHub Actions workflow.

### Setup

1. Ensure all secrets are configured in GitHub repository settings:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
   - `VERCEL_API_PROJECT_ID`
   - All API keys and database credentials

2. Push the deployment workflow file:
   ```bash
   git add .github/workflows/production-deploy.yml
   git commit -m "Add production deployment workflow"
   git push origin main
   ```

### Trigger Deployment

1. **Automatic**: Push to the `main` branch
2. **Manual**:
   - Go to Actions tab in your GitHub repository
   - Select "Production Deployment" workflow
   - Click "Run workflow"
   - Configure options (deploy frontend, API, AI services, run tests)
   - Click "Run"

### Monitor Deployment

1. Check GitHub Actions logs for progress
2. Each step will report its status
3. Upon completion, you'll receive an email notification

## Option 2: Local Scripted Deployment

You can deploy from your local machine using our deployment scripts.

### Setup

1. Ensure all environment variables are loaded:
   ```bash
   source ./scripts/source-env.sh
   ./scripts/validate-env-vars.sh production
   ```

2. Make scripts executable:
   ```bash
   chmod +x scripts/master-deploy.sh scripts/vercel-deploy.sh scripts/deploy-ai-services.sh
   ```

### Deployment

1. For complete deployment:
   ```bash
   ./scripts/master-deploy.sh production
   ```

2. For Vercel-specific deployment:
   ```bash
   ./scripts/vercel-deploy.sh production
   ```

3. For AI services deployment:
   ```bash
   ./scripts/deploy-ai-services.sh production
   ```

### Verification

Run the smoke tests:
```bash
node scripts/smoke-test.js production
```

## Option 3: Manual Deployment

If you prefer to deploy manually, follow these steps.

### Database Setup

1. Apply migrations to Supabase:
   ```bash
   npx supabase db push --db-url "$DATABASE_URL"
   ```

### Frontend Deployment

1. Navigate to the frontend directory:
   ```bash
   cd apps/web
   ```

2. Deploy to Vercel:
   ```bash
   vercel --prod --token $VERCEL_TOKEN
   ```

3. Set up custom domain:
   ```bash
   vercel alias set $(vercel ls --prod | head -n 1 | awk '{print $2}') justmaily.com
   ```

### API Deployment

1. Navigate to the API directory:
   ```bash
   cd apps/api
   ```

2. Deploy to Vercel:
   ```bash
   vercel --prod --token $VERCEL_TOKEN
   ```

3. Set up custom domain:
   ```bash
   vercel alias set $(vercel ls --prod | head -n 1 | awk '{print $2}') api.justmaily.com
   ```

### AI Services Deployment

1. Configure AI adapters:
   ```bash
   mkdir -p apps/api/ai/adapters/
   # Create configuration files manually as in deploy-ai-services.sh
   ```

2. Deploy AI components to Kubernetes:
   ```bash
   kubectl apply -f kubernetes/deployments/ai-service.yaml -n maily-production
   ```

## Post-Deployment Tasks

### 1. DNS Verification

Check DNS propagation for your domains:
```bash
dig justmaily.com
dig api.justmaily.com
```

### 2. Smoke Testing

Run the comprehensive smoke tests:
```bash
node scripts/smoke-test.js production
```

### 3. Manual Verification

Test critical user journeys:
- User authentication
- Email composition with AI assistance
- Blockchain verification
- Cross-platform features

### 4. Monitoring Setup

1. Access Grafana dashboards:
   ```
   https://grafana.justmaily.com
   ```

2. Set up alerts for critical metrics:
   - API response times
   - Error rates
   - Database performance
   - AI service availability

### 5. Backup Verification

Ensure backup systems are operational:
```bash
kubectl get cronjobs -n maily-production
```

## Troubleshooting

### Common Issues

#### Vercel Deployment Failures

**Problem**: Vercel deployment fails with build errors
**Solution**:
1. Check build logs in Vercel dashboard
2. Fix any TypeScript or dependency issues
3. Verify environment variables are correctly set

#### Database Connection Issues

**Problem**: API can't connect to database
**Solution**:
1. Verify database credentials in environment variables
2. Check if IP is allowed in Supabase dashboard
3. Test connection manually using `psql`

#### AI Service Errors

**Problem**: AI services return errors
**Solution**:
1. Check API keys in environment variables
2. Verify quota and rate limits with providers
3. Check AI adapter configuration files

### Rollback Procedure

If you need to roll back:

1. For Vercel deployments:
   ```bash
   vercel rollback --scope eipp
   ```

2. For database:
   ```bash
   ./scripts/db-migration.sh rollback production
   ```

3. Complete rollback:
   ```bash
   ./scripts/rollback.sh production previous-deployment-id
   ```

## Deployment Monitoring

To check the status of your deployment:

1. Vercel Deployments:
   - Visit [Vercel Dashboard](https://vercel.com/eipp)
   - Check deployment status and logs

2. Kubernetes Resources:
   ```bash
   kubectl get all -n maily-production
   ```

3. Database Status:
   - Check Supabase dashboard
   - Run health queries

4. System Health:
   ```bash
   curl https://api.justmaily.com/health
   ```

## Security Considerations

After deployment, perform these security checks:

1. Verify HTTPS is enforced on all endpoints
2. Test authentication flows
3. Verify API rate limiting is active
4. Confirm JWT expiration is properly handled
5. Test CORS policies

## Maintenance

Regular maintenance tasks:

1. API key rotation (every 90 days)
2. Certificate renewal monitoring
3. Database backups verification
4. Security patch application

## Next Steps

After successful deployment:

1. Set up monitoring alerts
2. Configure traffic analytics
3. Establish performance baselines
4. Set up regular security scanning

## Support

For deployment assistance, contact:
- Email: devops@justmaily.com
- Slack: #deployment-support
