# Maily Control Tool (mailyctl)

A unified command-line tool for managing the Maily platform across different environments. This tool provides functionality for deploying, verifying, testing, and maintaining all aspects of the Maily platform.

## Overview

The Maily Control Tool (mailyctl) is a comprehensive DevOps utility designed to manage the entire lifecycle of the Maily platform. It handles deployment, verification, testing, monitoring, and rollback operations for all Maily components across different environments. 

It now includes enhanced functionality for phased deployments, secret rotation, and service mesh verification, consolidating multiple separate scripts into a single, unified interface.

## Features

- **Component Management**: Deploy, verify, and monitor individual components or the entire platform
- **Environment Support**: Manage different environments (staging, production) with environment-specific configurations
- **Validation**: Pre-deployment validation to ensure components meet requirements
- **Verification**: Post-deployment verification to confirm successful deployment
- **Testing**: Run different scopes of tests (unit, integration, e2e, post-deployment)
- **Monitoring**: Check component status and view logs
- **Rollback**: Revert to previous versions if needed
- **Phased Deployments**: Orchestrate complex, multi-phase deployments from staging to production
- **Canary Releases**: Deploy with canary testing for gradual traffic migration
- **Secret Rotation**: Securely rotate credentials and secrets with Vault integration
- **Service Mesh Verification**: Comprehensive verification of Istio service mesh configuration

## Components

The tool manages the following Maily components:

- `frontend`: Next.js frontend application (deployed on Vercel)
- `api`: API service (deployed on Kubernetes)
- `ai-service`: AI service for email generation and analysis
- `websocket`: Canvas WebSocket server for real-time collaboration
- `blockchain`: Blockchain service for trust infrastructure
- `analytics`: Analytics service for user insights
- `campaign`: Campaign management service
- `email`: Email delivery service
- `workers`: Background processing workers
- `visualization-service`: Data visualization service
- `trust-verification`: Blockchain-based verification system
- `service-mesh`: Istio service mesh infrastructure

## Prerequisites

- Python 3.8+
- kubectl (for Kubernetes operations)
- Vercel CLI (for frontend deployments)
- Access to Maily Kubernetes clusters
- Appropriate environment variables and credentials

## Installation

1. Clone the Maily repository
2. Install required Python packages:

```bash
pip install -r requirements-mailyctl.txt
```

## Configuration

The tool uses configuration files located in the `config/` directory:

- `config.<environment>.yaml`: Environment-specific configuration
- `.env.<environment>`: Environment variables for the specified environment

## Usage

```
Usage:
  mailyctl.py deploy [--env=<environment>] [--version=<version>] [--components=<components>]
  mailyctl.py verify [--env=<environment>] [--version=<version>] [--components=<components>]
  mailyctl.py test [--env=<environment>] [--scope=<scope>]
  mailyctl.py status [--env=<environment>] [--components=<components>]
  mailyctl.py logs [--env=<environment>] [--components=<components>] [--tail=<lines>]
  mailyctl.py rollback [--env=<environment>] [--components=<components>] [--to-version=<version>]
  mailyctl.py config [--env=<environment>] [--show-secrets]
  mailyctl.py phased-deploy [--env=<environment>] [--version=<version>] [--skip-staging] [--start-phase=<phase>] [--end-phase=<phase>] [--dry-run] [--canary] [--canary-weight=<weight>]
  mailyctl.py secrets rotate [--env=<environment>] [--secret-types=<types>] [--notify]
  mailyctl.py verify-mesh [--env=<environment>] [--component=<component>] [--release=<release>]
  mailyctl.py (-h | --help)
  mailyctl.py --show-version

Options:
  -h --help                   Show this help message and exit.
  --show-version              Show version.
  --env=<environment>         Environment to target [default: staging].
  --components=<components>   Comma-separated list of components to target [default: all].
  --version=<version>         Version to deploy [default: latest].
  --scope=<scope>             Test scope (unit, integration, e2e, post-deployment) [default: all].
  --tail=<lines>              Number of log lines to show [default: 100].
  --to-version=<version>      Version to rollback to.
  --show-secrets              Show secrets in config output.
  --skip-staging              Skip staging deployment (phased-deploy only) [default: false].
  --start-phase=<phase>       Start phase (1-3) for phased deployment [default: 1].
  --end-phase=<phase>         End phase (1-3) for phased deployment [default: 3].
  --dry-run                   Run in dry-run mode without applying changes [default: false].
  --canary                    Deploy as a canary release [default: false].
  --canary-weight=<weight>    Traffic percentage for canary deployment [default: 10].
  --secret-types=<types>      Comma-separated list of secret types to rotate [default: all].
  --notify                    Send notifications after secret rotation [default: false].
  --component=<component>     Single component to verify service mesh [default: api].
  --release=<release>         Release name [default: maily].
```

## Examples

### Basic Commands

#### Deploy all components to staging

```bash
./mailyctl.py deploy --env=staging
```

#### Deploy specific components to production

```bash
./mailyctl.py deploy --env=production --components=api,ai-service --version=1.2.3
```

#### Verify deployment in staging

```bash
./mailyctl.py verify --env=staging
```

#### Run post-deployment tests in production

```bash
./mailyctl.py test --env=production --scope=post-deployment
```

#### Check component status

```bash
./mailyctl.py status --env=staging --components=websocket,blockchain
```

#### View logs for a component

```bash
./mailyctl.py logs --env=production --components=api --tail=200
```

#### Rollback a component to a previous version

```bash
./mailyctl.py rollback --env=production --components=frontend --to-version=1.1.0
```

#### Show configuration

```bash
./mailyctl.py config --env=staging
```

### Enhanced Commands

#### Phased deployment to staging and production

```bash
# Full phased deployment across all environments
./mailyctl.py phased-deploy --version=1.2.3

# Skip staging and deploy directly to production
./mailyctl.py phased-deploy --version=1.2.3 --skip-staging

# Start from phase 2 (initial production)
./mailyctl.py phased-deploy --version=1.2.3 --start-phase=2

# Canary deployment with 20% traffic
./mailyctl.py phased-deploy --version=1.2.3 --canary --canary-weight=20

# Dry run without making changes
./mailyctl.py phased-deploy --version=1.2.3 --dry-run
```

#### Secret rotation

```bash
# Rotate all secrets
./mailyctl.py secrets rotate --env=production

# Rotate specific secret types
./mailyctl.py secrets rotate --env=production --secret-types=database,jwt,api_keys

# Rotate secrets and send notifications
./mailyctl.py secrets rotate --env=production --notify
```

#### Service mesh verification

```bash
# Verify service mesh for default component (api)
./mailyctl.py verify-mesh --env=staging

# Verify service mesh for specific component
./mailyctl.py verify-mesh --env=production --component=ai-service

# Verify service mesh with specific release name
./mailyctl.py verify-mesh --env=production --component=api --release=maily-prod
```

## Validation and Verification

The tool uses validator and verifier scripts located in the `system/` directory:

- `validators/`: Scripts that validate components before deployment
- `verifiers/`: Scripts that verify components after deployment

## Deployment Methods

The tool supports different deployment methods:

- **Kubernetes**: For backend services and microservices
- **Vercel**: For the frontend application
- **Helm**: For Kubernetes applications with Helm charts
- **Service Mesh**: Istio-based service mesh deployments with traffic management
- **ArgoCD**: GitOps-based deployment with ArgoCD

The phased deployment process implemented in the tool combines these methods to provide a comprehensive deployment pipeline from staging to production, with proper testing and verification at each stage.

## Logging

The tool logs all operations to the console with detailed information about each step.

## Error Handling

The tool provides detailed error messages and warnings to help diagnose issues.

## New Features

### Phased Deployment

The phased deployment feature provides a sophisticated deployment pipeline with three distinct phases:

1. **Phase 1 - Testing & Validation (Staging)**
   - Deploy to staging environment
   - Run automated tests and chaos testing
   - Verify monitoring and alerting
   - Deploy service mesh components

2. **Phase 2 - Initial Production (Non-Critical Services)**
   - Deploy non-critical services first
   - Apply resource limits and probes
   - Configure logging and tracing
   - Monitor performance impacts

3. **Phase 3 - Full Production (Critical Services)**
   - Deploy critical services
   - Implement secret rotation
   - Enable full SLA monitoring
   - Apply service mesh security policies

### Secret Rotation

The secret rotation functionality integrates with HashiCorp Vault to securely rotate and manage secrets:

- Rotate database credentials
- Update JWT secrets
- Manage API keys
- Refresh AWS credentials
- Update SMTP settings

### Service Mesh Verification

The service mesh verification feature provides comprehensive validation of Istio service mesh components:

- Verify Istio installation and version
- Check mTLS configuration and enforcement
- Validate circuit breaker configuration
- Verify virtual services and routing rules
- Check deployment health
- Run Istio analyzer for configuration issues

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Submit a pull request

## License

Proprietary - All rights reserved
