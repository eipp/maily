# Maily Control Tool (mailyctl)

A command-line tool for managing the Maily platform across different environments. This tool provides functionality for deploying, verifying, and testing Maily components.

## Overview

The Maily Control Tool (mailyctl) is a comprehensive DevOps utility designed to manage the entire lifecycle of the Maily platform. It handles deployment, verification, testing, monitoring, and rollback operations for all Maily components across different environments.

## Features

- **Component Management**: Deploy, verify, and monitor individual components or the entire platform
- **Environment Support**: Manage different environments (staging, production) with environment-specific configurations
- **Validation**: Pre-deployment validation to ensure components meet requirements
- **Verification**: Post-deployment verification to confirm successful deployment
- **Testing**: Run different scopes of tests (unit, integration, e2e, post-deployment)
- **Monitoring**: Check component status and view logs
- **Rollback**: Revert to previous versions if needed

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
  mailyctl.py (-h | --help)
  mailyctl.py --version

Options:
  -h --help                 Show this help message and exit.
  --version                 Show version.
  --env=<environment>       Environment to target [default: staging].
  --components=<components> Comma-separated list of components to target [default: all].
  --version=<version>       Version to deploy [default: latest].
  --scope=<scope>           Test scope (unit, integration, e2e, post-deployment) [default: all].
  --tail=<lines>            Number of log lines to show [default: 100].
  --to-version=<version>    Version to rollback to.
  --show-secrets            Show secrets in config output.
```

## Examples

### Deploy all components to staging

```bash
python mailyctl.py deploy --env=staging
```

### Deploy specific components to production

```bash
python mailyctl.py deploy --env=production --components=api,ai-service --version=1.2.3
```

### Verify deployment in staging

```bash
python mailyctl.py verify --env=staging
```

### Run post-deployment tests in production

```bash
python mailyctl.py test --env=production --scope=post-deployment
```

### Check component status

```bash
python mailyctl.py status --env=staging --components=websocket,blockchain
```

### View logs for a component

```bash
python mailyctl.py logs --env=production --components=api --tail=200
```

### Rollback a component to a previous version

```bash
python mailyctl.py rollback --env=production --components=frontend --to-version=1.1.0
```

### Show configuration

```bash
python mailyctl.py config --env=staging
```

## Validation and Verification

The tool uses validator and verifier scripts located in the `system/` directory:

- `validators/`: Scripts that validate components before deployment
- `verifiers/`: Scripts that verify components after deployment

## Deployment Methods

The tool supports different deployment methods:

- **Kubernetes**: For backend services and microservices
- **Vercel**: For the frontend application

## Logging

The tool logs all operations to the console with detailed information about each step.

## Error Handling

The tool provides detailed error messages and warnings to help diagnose issues.

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Submit a pull request

## License

Proprietary - All rights reserved
