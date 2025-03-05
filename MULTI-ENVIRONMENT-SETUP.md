# Multi-Environment Setup for Maily

This document provides comprehensive guidance on Maily's multi-environment deployment architecture. It covers all necessary configurations and deployment processes for each environment.

## Environments Overview

| Environment | Purpose | Branch | Domain Pattern | Resource Level |
|-------------|---------|--------|----------------|---------------|
| Production  | Live customer-facing environment | `main` | justmaily.com | Full scale |
| Staging     | Pre-production testing | `staging` | staging-*.justmaily.com | Near production |
| Testing     | QA and integration testing | `testing` | test-*.justmaily.com | Medium scale |
| Development | Development and feature testing | `develop` | dev-*.justmaily.com | Minimal |

## DNS Configuration

All environments are configured with the following subdomains:

- **Production**: 
  - Main site: justmaily.com
  - Web app: app.justmaily.com
  - API: api.justmaily.com
  - Analytics: analytics.justmaily.com
  - CDN: cdn.justmaily.com

- **Staging**:
  - Main site: staging.justmaily.com
  - Web app: staging-app.justmaily.com
  - API: staging-api.justmaily.com
  - Analytics: staging-analytics.justmaily.com
  - CDN: staging-cdn.justmaily.com

- **Testing**:
  - Main site: test.justmaily.com
  - Web app: test-app.justmaily.com
  - API: test-api.justmaily.com
  - Analytics: test-analytics.justmaily.com
  - CDN: test-cdn.justmaily.com

- **Development**:
  - Main site: dev.justmaily.com
  - Web app: dev-app.justmaily.com
  - API: dev-api.justmaily.com
  - Analytics: dev-analytics.justmaily.com
  - CDN: dev-cdn.justmaily.com

## AWS Infrastructure

### Terraform Configuration

Each environment has its own Terraform variable file:
- `/infrastructure/terraform/production.tfvars`
- `/infrastructure/terraform/staging.tfvars`
- `/infrastructure/terraform/testing.tfvars`
- `/infrastructure/terraform/development.tfvars`

To apply infrastructure changes for a specific environment:

```bash
cd infrastructure/terraform
terraform workspace select <environment>
terraform apply -var-file=<environment>.tfvars
```

### Database Configuration

Each environment has its own RDS instance:
- Production: maily-prod.cluster-xyz.us-west-2.rds.amazonaws.com
- Staging: maily-staging.cluster-xyz.us-west-2.rds.amazonaws.com
- Testing: maily-test.cluster-xyz.us-west-2.rds.amazonaws.com
- Development: maily-dev.cluster-xyz.us-west-2.rds.amazonaws.com

### Kubernetes Configuration

Each environment has its own namespace:
- Production: maily-production
- Staging: maily-staging
- Testing: maily-test
- Development: maily-dev

Deployment files are located in:
- `/kubernetes/production/maily-deployment.yaml`
- `/kubernetes/staging/maily-deployment.yaml`
- `/kubernetes/testing/maily-deployment.yaml`
- `/kubernetes/development/maily-deployment.yaml`

## Vercel Deployment

### Configuration Files

Each environment has its own Vercel configuration:

- **Web App**:
  - `/apps/web/vercel.production.json`
  - `/apps/web/vercel.staging.json`
  - `/apps/web/vercel.testing.json`
  - `/apps/web/vercel.development.json`

- **API**:
  - `/apps/api/vercel.production.json`
  - `/apps/api/vercel.staging.json`
  - `/apps/api/vercel.testing.json`
  - `/apps/api/vercel.development.json`

### Deployment Commands

To deploy to a specific environment:

```bash
# For web app
cd apps/web
vercel --prod -e NODE_ENV=<environment> --build-env NODE_ENV=<environment> --local-config vercel.<environment>.json

# For API
cd apps/api
vercel --prod -e NODE_ENV=<environment> --build-env NODE_ENV=<environment> --local-config vercel.<environment>.json
```

## Supabase Configuration

Each environment has its own Supabase project. Database URLs are configured in the environment files:

- Production: See production environment files
- Staging: See staging environment files
- Testing: See testing environment files
- Development: See development environment files

## Environment Files

Environment files for each environment:

- **Web App**:
  - `/apps/web/.env.production`
  - `/apps/web/.env.staging`
  - `/apps/web/.env.test`
  - `/apps/web/.env.development`

- **API**:
  - `/apps/api/.env.production`
  - `/apps/api/.env.staging`
  - `/apps/api/.env.test`
  - `/apps/api/.env.development`

## CI/CD Workflow

The GitHub Actions workflow in `.github/workflows/unified-ci-cd.yml` supports all environments. It automatically determines the deployment environment based on the branch:

- `main` → Production
- `staging` → Staging
- `testing` → Testing
- `develop` → Development

You can also manually trigger a deployment to any environment using the workflow dispatch trigger.

## Setting Up a New Environment

To set up a new environment:

1. Create DNS records for all required subdomains
2. Create Terraform variables file in `/infrastructure/terraform/<environment>.tfvars`
3. Create Kubernetes namespace and deployment files
4. Create Vercel configuration files
5. Create environment variables files
6. Configure Supabase project
7. Update CI/CD workflow if needed

## Environment-Specific Considerations

### Production
- Highest resource allocation
- Multi-AZ deployment
- Strict security measures
- Regular backups

### Staging
- Near-production resources
- Used for final testing before production
- Data refreshed from production periodically

### Testing
- Medium resources
- Used for QA and integration testing
- Test data generated through scripts

### Development
- Minimal resources
- Used for development and feature testing
- Frequent redeployments 

## Feature Flags System

Maily uses a robust feature flag system to control feature availability across environments. This allows us to deploy code to production while controlling which features are visible to users.

### Feature Flag Configuration

Feature flags are defined in `/config/feature-flags.js` with environment-specific settings:

```javascript
{
  'feature-name': {
    description: 'Feature description',
    enabledIn: ['development', 'testing', 'staging'], // environments where enabled
    rolloutPercentage: {  // gradual rollout control
      development: 100,
      testing: 100,
      staging: 50,
      production: 0
    }
  }
}
```

### Using Feature Flags

#### Backend (API)
```javascript
const { isFeatureEnabled } = require('../../config/feature-flags');

if (isFeatureEnabled('feature-name', { userID: req.user.id })) {
  // Execute feature code
}
```

#### Frontend (React)
```jsx
import { useFeatureFlag } from '../hooks/useFeatureFlag';

function MyComponent() {
  const { enabled, loading } = useFeatureFlag('feature-name');
  
  if (loading) return <Loading />;
  
  return enabled ? <NewFeature /> : <OldFeature />;
}
```

### Feature Flag API

The API provides endpoints to fetch feature flag status:
- `GET /api/features` - Get all feature flags (requires authentication)
- `GET /api/features/:featureName` - Get specific feature flag status
- `GET /api/features/public` - Get public feature flags (no auth required)

## Database Migration Between Environments

Maily includes a database migration script that safely transfers schema and data between environments.

### Migration Script Usage

```bash
./scripts/migrate-database.sh <source_env> <target_env> [options]

# Examples:
./scripts/migrate-database.sh staging production --backup
./scripts/migrate-database.sh development testing --schema-only
./scripts/migrate-database.sh staging production --dry-run
```

### Options

- `--dry-run`: Show what would be done without making changes
- `--schema-only`: Migrate only the database schema (tables, indexes, etc.)
- `--with-seed-data`: Include seed/demo data in migration
- `--backup`: Create a backup before migration (required for production)

### Migration Safety Features

- Production migrations require a backup by default
- Dry run option to validate migrations before applying
- Automatic database URL extraction from environment files
- Clear error reporting and progress logging

## Monitoring & Observability

### Prometheus Configuration

Maily uses Prometheus for metrics collection across all environments. Configuration is stored in:
- `/kubernetes/monitoring/prometheus-values.yaml`

The configuration includes:
- Environment-specific scrape jobs
- Different alert thresholds by environment
- Alert routing to Slack and PagerDuty

### Alert Rules

Different alerting thresholds are used per environment:
- Production: Stricter thresholds (e.g., 1% error rate triggers critical alert)
- Non-production: More relaxed thresholds (e.g., 5% error rate for warning, 15% for critical)

### Alert Notifications

- Slack: All alerts go to the #maily-alerts channel
- PagerDuty: Only critical alerts trigger paging

### Installing Monitoring

```bash
helm upgrade --install prometheus prometheus-community/prometheus -f kubernetes/monitoring/prometheus-values.yaml -n monitoring
```

## Deployment Scripts

Maily includes scripts to facilitate deployment across environments:

### Environment Deployment

```bash
./scripts/deploy-environment.sh [environment] [component]

# Examples:
./scripts/deploy-environment.sh production web
./scripts/deploy-environment.sh staging api
./scripts/deploy-environment.sh testing all
```

The script handles deployment of web, API, or all components to the specified environment. 