# Maily DevOps Documentation

## Overview

This document consolidates all DevOps-related documentation for the Maily platform. It covers the strategic approach, infrastructure, deployment processes, monitoring, and emergency procedures.

## Table of Contents

1. [DevOps Strategy](#devops-strategy)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Deployment System](#deployment-system)
4. [Monitoring](#monitoring)
5. [Security](#security)
6. [Disaster Recovery](#disaster-recovery)
7. [Emergency Rollback](#emergency-rollback)

## DevOps Strategy

### Infrastructure Architecture

Maily consists of these key components:

- **Frontend**: Next.js 14+ with TypeScript and Tailwind CSS
- **API Backend**: FastAPI with PostgreSQL + SQLAlchemy ORM
- **AI Service**: OctoTools framework with adapter pattern for multiple LLM providers
- **Email Services**: Support for Resend, SendGrid, and Mailgun
- **Analytics**: Performance monitoring and user engagement metrics
- **Real-time Canvas Collaboration**: WebSocket-based real-time collaboration
- **Blockchain Integration**: Trust infrastructure and smart contracts

Infrastructure as Code is managed via:
- **Terraform**: AWS EKS, RDS, ElastiCache, S3, CloudFront, VPC
- **Kubernetes**: Deployments, HPA, Service Mesh, PVCs

### CI/CD Pipeline

The CI/CD pipeline uses GitHub Actions with:

1. **Lint and Type Check**: ESLint, TypeScript, Black, isort, flake8
2. **Testing**: Unit, integration, E2E tests
3. **Security Scanning**: npm audit, Trivy, OWASP ZAP
4. **Build**: Docker images, Next.js optimization
5. **Deployment**: Staging → Production (with approval)

Deployment strategies include:
- Blue/Green Deployment for zero downtime
- Canary Releases for gradual rollout
- Feature Flags for controlled releases

### Monitoring

The monitoring stack includes:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation
- **Datadog**: RUM and APM

Key metrics tracked:
- Infrastructure: CPU, memory, network
- Application: Request rates, latencies, errors
- AI Service: Inference latency, token usage
- Blockchain: Transaction success, gas usage

### Security & Compliance

Implemented security measures:
- Vault for secrets management
- TLS for all communications
- Network Policies for service isolation
- RBAC for access control
- WAF for web protection
- Automated security scanning

Compliance with GDPR, CCPA, SOC 2

## Infrastructure Setup

Infrastructure setup is automated with the `scripts/setup-devops-infrastructure.sh` script, which handles:

- AWS credentials configuration
- Terraform backend setup
- EKS cluster setup
- Kubernetes namespaces
- Vault for secrets management
- Monitoring setup
- CI/CD setup
- Docker registry setup
- Vercel setup

Usage:
```bash
chmod +x scripts/setup-devops-infrastructure.sh
./scripts/setup-devops-infrastructure.sh
```

## Deployment System

The Maily Unified Deployment System provides a robust, phased approach to ensure production readiness.

### Production Readiness Features

- **Versioned Docker Images**: Specific version tags instead of 'latest'
- **Security**: SAST/DAST integration, secret rotation, audits
- **Health Checks**: Liveness/readiness probes, resource limits, SLA monitoring
- **Resilience**: Chaos testing, load testing, circuit breakers, distributed tracing

### System Components

- `scripts/maily-deploy.sh`: Main controller script
- `scripts/deploy-phases/phase1-staging.sh`: Staging deployment
- `scripts/deploy-phases/phase2-prod-initial.sh`: Non-critical services
- `scripts/deploy-phases/phase3-prod-full.sh`: Critical services

### Usage

Basic deployment:
```bash
./scripts/maily-deploy.sh --version v1.0.0
```

Options:
```
--help                    Show help message
--version VERSION         Set deployment version
--dry-run                 Execute without changes
--skip-staging            Skip to production
--skip-confirmation       Non-interactive mode
--skip-monitoring         Skip monitoring waits
--start-phase PHASE       Start at phase (1-3)
--end-phase PHASE         End at phase (1-3)
--staging-namespace NAME  Set staging namespace
--prod-namespace NAME     Set production namespace
```

### Deployment Phases

1. **Testing & Validation (Staging)**
   - Deploy to staging
   - Run automated tests
   - Security and chaos testing
   - Performance verification

2. **Initial Production (Non-Critical Services)**
   - Deploy non-critical services
   - Apply resource limits and health probes
   - Configure secret rotation
   - Setup monitoring

3. **Full Production (Critical Services)**
   - Deploy critical services
   - Apply network policies
   - Enable SLA monitoring
   - Implement distributed tracing

### Utilities

**Image Tag Update**: `scripts/update-image-tags.sh`
```bash
./scripts/update-image-tags.sh --version v2.1.0
```

**Deployment Validator**: `scripts/deployment-validator.sh`
```bash
./scripts/deployment-validator.sh --environment production
```

**Configuration Collector**: `scripts/config-collector.sh`
```bash
./scripts/config-collector.sh --environment production
```

## Monitoring

Monitoring is set up with Datadog using the `scripts/setup-datadog-monitoring.sh` script.

Usage:
```bash
export DATADOG_API_KEY=your_api_key
export DATADOG_APP_KEY=your_app_key
./scripts/setup-datadog-monitoring.sh
```

## Disaster Recovery

Recovery procedures include:
- Database backups with point-in-time recovery
- S3 backups for files
- Configuration backups
- Automated and manual failover

Recovery objectives:
- RTO: 1 hour
- RPO: 15 minutes

## Emergency Rollback

### Prerequisites
- Kubernetes cluster access
- Vercel CLI configured
- Redis CLI configured
- Environment variables set

### Quick Rollback Commands

**Full System Rollback**:
```bash
./scripts/rollback-production.sh
```

**Individual Service Rollbacks**:
```bash
# API Service
kubectl rollout undo deployment/maily-api

# AI Service
kubectl rollout undo deployment/ai-mesh

# Frontend
vercel rollback --project=maily-web
```

**Database Rollbacks**:
```bash
# Latest snapshot
./scripts/restore-db-snapshot.sh latest

# Specific date
./scripts/restore-db-snapshot.sh 2025-04-03
```

### Post-Rollback Actions

1. Create an incident report
2. Coordinate with development team
3. Plan a new deployment with fixes