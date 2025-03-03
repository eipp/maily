# GitHub Actions Migration Workflow Reference

## Overview

This document provides a reference guide for the GitHub Actions workflow used to automate database migrations in the Maily project. The workflow is defined in `.github/workflows/migrations.yml` and handles validation, testing, and deployment of database migrations.

## Workflow Triggers

The workflow is triggered by:

1. **Push to main**: When changes are pushed to the main branch that affect migration files
   ```yaml
   push:
     branches:
       - main
     paths:
       - 'supabase/migrations/**'
       - 'scripts/**'
   ```

2. **Pull Requests**: When PRs include changes to migration files
   ```yaml
   pull_request:
     paths:
       - 'supabase/migrations/**'
       - 'scripts/**'
   ```

3. **Manual Dispatch**: Allows manually triggering migrations with environment selection
   ```yaml
   workflow_dispatch:
     inputs:
       environment:
         description: 'Environment to deploy migrations to'
         required: true
         default: 'development'
         type: choice
         options:
           - development
           - staging
           - production
   ```

## Jobs

### Validate Job

The `validate` job runs on all triggers and validates migrations against a test database:

```yaml
validate:
  name: Validate migrations
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:14
      env:
        POSTGRES_PASSWORD: postgres
        POSTGRES_USER: postgres
        POSTGRES_DB: maily_test
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
```

Key steps in the validation job:

1. **Checkout code**
2. **Setup Node.js and dependencies**
3. **Install Supabase CLI**
4. **Setup test environment**
5. **Apply migrations**
6. **Validate schema**

This job exits with an error if migrations are invalid, preventing merges that would break the database schema.

### Deploy Job

The `deploy` job only runs on pushes to main or manual dispatch events:

```yaml
deploy:
  name: Deploy migrations
  needs: validate
  if: github.event_name == 'workflow_dispatch' || (github.event_name == 'push' && github.ref == 'refs/heads/main')
  runs-on: ubuntu-latest
  environment: ${{ github.event.inputs.environment || 'development' }}
```

Key steps in the deploy job:

1. **Checkout code**
2. **Setup Node.js and dependencies**
3. **Install Supabase CLI**
4. **Check for migrations**
5. **Deploy migrations** (if needed)
6. **Notify on success/failure**

## Environment Selection

When triggered manually, you can select the target environment:

1. **Development**: Default environment, used for testing
2. **Staging**: Pre-production environment for final testing
3. **Production**: Live environment (requires manual approval)

## Environment Secrets

The workflow uses the following repository secrets:

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  DATABASE_HOST: ${{ secrets.DATABASE_HOST }}
  DATABASE_PORT: ${{ secrets.DATABASE_PORT }}
  DATABASE_NAME: ${{ secrets.DATABASE_NAME }}
  DATABASE_USER: ${{ secrets.DATABASE_USER }}
  DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
```

Each environment (development, staging, production) has its own set of these secrets.

## Migration Validation

The validation process ensures:

1. Migrations apply cleanly to a fresh database
2. Rollbacks work correctly
3. Migration history is properly tracked
4. No conflicts exist between migrations

## Manual Workflow Dispatch

To manually run migrations:

1. Go to the Actions tab in GitHub
2. Select "Database Migrations" workflow
3. Click "Run workflow"
4. Select the target environment
5. Click "Run workflow" button

This is the recommended way to deploy migrations to production.

## Workflow Diagram

```
┌─────────────────┐
│   Trigger:      │
│  - Push to main │
│  - Pull request │
│  - Manual       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    validate     │
│  - Check schema │
│  - Test apply   │
│  - Test rollback│
└────────┬────────┘
         │
         ▼
┌─────────────────┐      No      ┌─────────────┐
│   Successful?   ├─────────────►│ Fail build  │
└────────┬────────┘              └─────────────┘
         │ Yes
         │
         ▼
┌─────────────────┐      No      ┌─────────────┐
│  Deploy needed? ├─────────────►│    Done     │
└────────┬────────┘              └─────────────┘
         │ Yes
         │
         ▼
┌─────────────────┐
│     deploy      │
│ - Apply changes │
│ - Update history│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Notify       │
└─────────────────┘
```

## Testing Locally

To test the workflow locally before pushing:

```bash
# Check migrations
./scripts/check-migrations.sh development

# Apply migrations
./scripts/db-migration.sh development migrate
```

## Troubleshooting

### Failed Validation

If validation fails:
1. Check the workflow logs for error messages
2. Fix the migration issues
3. Push the updated migrations
4. Re-run the workflow

### Failed Deployment

If deployment fails:
1. Check the database logs
2. Fix any issues with the migrations
3. Re-run the workflow

### Manual Recovery

For emergency recovery:
1. SSH to the database server
2. Apply manual fixes
3. Update the migration history table
4. Push the corresponding migrations to the repository 