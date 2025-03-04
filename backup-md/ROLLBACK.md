# Maily Emergency Rollback Guide

This document provides quick commands for emergency rollbacks if issues are detected in production. Use these commands with caution and only when necessary.

## Prerequisites

Ensure you have the proper credentials and access:
- Kubernetes cluster access configured
- Vercel CLI configured and logged in
- Redis CLI configured
- Proper environment variables set

## Quick Rollback Commands

### 1. Full Backend and Frontend Rollback

```bash
# Execute full rollback script
./scripts/rollback-production.sh
```

### 2. Individual Service Rollbacks

#### Kubernetes Services

```bash
# Rollback API service to previous version
kubectl rollout undo deployment/maily-api

# Rollback AI service to previous version
kubectl rollout undo deployment/ai-mesh

# Rollback email service to previous version
kubectl rollout undo deployment/email-service
```

#### Vercel Frontend

```bash
# Rollback the web frontend (using project ID)
vercel rollback --project=maily-web

# Alternative with team
vercel rollback --project=maily-web --scope=your-team
```

### 3. Database Rollbacks

```bash
# Restore database from the latest snapshot
./scripts/restore-db-snapshot.sh latest

# Restore database from a specific date
./scripts/restore-db-snapshot.sh 2025-04-03
```

## Monitoring During Rollback

After performing a rollback, monitor these critical metrics:

1. API service response times and error rates
2. AI service performance
3. Blockchain verification success rate
4. Redis operation latency
5. User login success rate

To check service health quickly:

```bash
# Check all deployment statuses
kubectl get deployments

# Check service logs for errors
kubectl logs -l app=maily-api --tail=100
kubectl logs -l app=ai-mesh --tail=100

# Check Datadog metrics
./scripts/check-critical-metrics.sh
```

## Post-Rollback Actions

After a successful rollback:

1. Create an incident report documenting:
   - Time of incident
   - Observed symptoms
   - Actions taken
   - Root cause (if identified)

2. Coordinate with the development team to fix the issue

3. Plan a new deployment with the fix

## Support

For urgent assistance, contact:
- DevOps Team: devops@maily.example.com
- Engineering Lead: engineering@maily.example.com