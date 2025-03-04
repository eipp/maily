# Maily Unified Deployment System

This document provides comprehensive documentation for the Maily Unified Deployment System - a robust, phased deployment process designed to ensure production readiness and reliability.

## Table of Contents

1. [Overview](#overview)
2. [Production Readiness Features](#production-readiness-features)
3. [System Components](#system-components)
4. [Usage](#usage)
5. [Deployment Phases](#deployment-phases)
6. [Utilities](#utilities)
7. [Troubleshooting](#troubleshooting)
8. [Contributing](#contributing)

## Overview

The Maily Unified Deployment System provides a comprehensive approach to deploying Maily services from testing through to production. It implements a phased deployment process with robust validation at each stage, ensuring all production readiness requirements are met before completing deployment.

## Production Readiness Features

This system implements all required production readiness features:

### Docker Image Tags
- **✅ Versioned Image Tags**: All `latest` tags are replaced with specific version numbers (e.g., `v1.0.0`) using the `update-image-tags.sh` utility.
- **✅ Consistent Deployments**: Ensures all environments use the same, pinned versions.

### Security
- **✅ SAST/DAST in CI/CD**: Integrated security scanning during deployment pipeline.
- **✅ Secret Rotation**: Automated secret rotation for database credentials, API keys, etc.
- **✅ Automated Security Audits**: Regular scheduled security scanning.

### Health & Monitoring
- **✅ Liveness/Readiness Probes**: Health check configuration for all services.
- **✅ Resource Limits**: Resource requests and limits for all containers.
- **✅ SLA Monitoring**: Deployment of monitoring dashboards and alerts.
- **✅ Structured Logging**: Standardized logging format across all services.

### Resilience
- **✅ Chaos Testing**: Scheduled chaos experiments to verify resilience.
- **✅ Automated Load Testing**: Regular load tests to ensure performance.
- **✅ Circuit Breakers**: Protection against cascading failures.
- **✅ Distributed Tracing**: Service interaction and latency tracking.

### Documentation
- **✅ Operational Runbooks**: Documented procedures for common issues.
- **✅ Interactive API Documentation**: Deployment of API documentation.
- **✅ Browser Compatibility Testing**: Automated cross-browser validation.

## System Components

The Maily Unified Deployment System consists of the following components:

### Core Scripts

- `scripts/maily-deploy.sh`: Main controller script orchestrating the deployment process
- `scripts/deploy-phases/phase1-staging.sh`: Staging deployment and testing phase
- `scripts/deploy-phases/phase2-prod-initial.sh`: Initial production deployment (non-critical services)
- `scripts/deploy-phases/phase3-prod-full.sh`: Full production deployment (critical services)

### Utilities

- `scripts/update-image-tags.sh`: Replaces 'latest' tags with specific version numbers
- `scripts/config-collector.sh`: Interactively collects configuration values
- `scripts/deployment-validator.sh`: Validates deployment configuration

## Usage

### Basic Deployment

To perform a standard deployment:

```bash
./scripts/maily-deploy.sh --version v1.0.0
```

This will perform the complete three-phase deployment process:
1. Deploy to staging and run tests
2. Deploy non-critical services to production
3. Deploy critical services to production

### Options

The deployment script supports several options:

```
--help                    Show the help message
--version VERSION         Set deployment version (default: v1.0.0)
--dry-run                 Execute in dry-run mode without applying changes
--skip-staging            Skip staging deployment and go straight to production
--skip-confirmation       Run without confirmation prompts (non-interactive mode)
--skip-monitoring         Skip monitoring wait periods
--start-phase PHASE       Start at specified phase (1-3)
--end-phase PHASE         End at specified phase (1-3)
--staging-namespace NAME  Set staging namespace (default: maily-staging)
--prod-namespace NAME     Set production namespace (default: maily-production)
```

### Example Commands

```bash
# Test without applying changes
./scripts/maily-deploy.sh --dry-run

# Deploy specific version
./scripts/maily-deploy.sh --version v2.1.0

# Skip staging and deploy directly to production
./scripts/maily-deploy.sh --skip-staging

# Start from phase 2 (initial production)
./scripts/maily-deploy.sh --start-phase 2
```

## Deployment Phases

The deployment process consists of three distinct phases:

### Phase 1: Testing & Validation (Staging)

- Deploys all changes to staging environment
- Runs automated tests to validate changes
- Runs security tests (SAST/DAST)
- Performs chaos testing to validate resilience
- Runs load tests to verify performance
- Verifies SLA monitoring and alerting

### Phase 2: Initial Production Deployment (Non-Critical Services)

- Deploys non-critical services to production
- Applies resource limits and health probes
- Configures automated secret rotation
- Deploys structured logging configuration
- Deploys autoscaling configuration
- Monitors for performance impacts

### Phase 3: Full Production Deployment (Critical Services)

- Deploys critical services to production
- Applies network policies
- Enables SLA monitoring in production
- Schedules chaos testing for resilience validation
- Implements distributed tracing
- Deploys interactive API documentation
- Sets up automated load testing
- Finalizes operational runbooks
- Schedules regular security audits
- Sets up browser compatibility testing

## Utilities

### Image Tag Update Utility

The image tag update utility (`scripts/update-image-tags.sh`) replaces 'latest' Docker image tags with specific version numbers in Kubernetes manifest files.

Usage:
```bash
./scripts/update-image-tags.sh [options]
```

Options:
```
-h, --help                 Show the help message
-v, --version VERSION      Set the version number to use (default: v1.0.0)
-d, --directory DIR        Set the target directory (default: kubernetes)
--no-backup                Don't create backup files
--dry-run                  Run without making changes
```

Examples:
```bash
# Replace 'latest' with 'v2.1.0'
./scripts/update-image-tags.sh --version v2.1.0

# Target the 'k8s' directory
./scripts/update-image-tags.sh --directory k8s

# Test without making changes
./scripts/update-image-tags.sh --dry-run
```

### Deployment Validator

The deployment validator (`scripts/deployment-validator.sh`) checks deployment configuration for issues such as missing configuration values, mock data, and required Kubernetes resources.

Usage:
```bash
./scripts/deployment-validator.sh [options]
```

Options:
```
-e, --environment ENV      Set the environment (default: production)
-c, --config-dir DIR       Set the configuration directory (default: config)
```

### Configuration Collector

The configuration collector (`scripts/config-collector.sh`) interactively collects configuration values and saves them to the appropriate configuration file.

Usage:
```bash
./scripts/config-collector.sh [options]
```

Options:
```
-e, --environment ENV      Set the environment (default: production)
-o, --output FILE          Set the output file (default: .env.ENV)
-f, --format FORMAT        Set the format (env, json, yaml) (default: env)
```

## Troubleshooting

### Common Issues

#### Deployment fails at phase 1 (staging)
- Check the staging environment for issues
- Verify test results
- Check for resource constraints

#### Secret rotation issues
- Verify Vault is properly configured
- Check secret permissions
- Validate rotation scripts

#### Monitoring doesn't show data
- Verify Prometheus/Grafana setup
- Check service annotations for scraping
- Validate metrics endpoint exposure

### Log Files

The deployment process generates detailed logs in the `deployment_logs` directory. Each deployment run creates a timestamped log file with full details of the execution.

## Contributing

To contribute to the deployment system:

1. Create a feature branch
2. Make your changes
3. Test your changes using the `--dry-run` option
4. Submit a pull request

Please follow the established coding style and include appropriate documentation for any new features.
