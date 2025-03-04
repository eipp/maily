# Maily Repository Structure

This document outlines the standardized structure of the Maily repository.

## Directory Structure

```
maily/
├── apps/                    # Application services
│   ├── ai-service/          # AI service
│   │   └── src/             # Source code
│   ├── api/                 # API service
│   │   └── src/             # Source code
│   ├── email-service/       # Email service
│   │   └── src/             # Source code
│   ├── web/                 # Web frontend
│   │   └── src/             # Source code
│   └── workers/             # Background workers
│       └── src/             # Source code
│
├── config/                  # Centralized configuration
│   ├── app/                 # Application-specific config
│   ├── services/            # Shared services config
│   ├── shared/              # Shared configuration
│   └── environments/        # Environment-specific config
│
├── docker/                  # Docker configuration
│   ├── compose/             # Docker Compose files
│   ├── dockerfiles/         # Standardized Dockerfiles
│   └── templates/           # Dockerfile templates
│
├── docs/                    # Documentation
│   ├── adr/                 # Architecture Decision Records
│   ├── api/                 # API documentation
│   ├── development/         # Development guides
│   └── runbooks/            # Operations runbooks
│
├── infrastructure/          # Infrastructure as code
│   ├── kubernetes/          # Kubernetes manifests
│   ├── terraform/           # Terraform configurations
│   └── helm/                # Helm charts
│
├── kubernetes/              # Kubernetes configurations
│   ├── deployments/         # Deployment manifests
│   ├── services/            # Service manifests
│   └── monitoring/          # Monitoring configurations
│
├── packages/                # Shared packages
│   ├── analytics/           # Analytics utilities
│   ├── api-client/          # API client
│   ├── config/              # Configuration utilities
│   ├── database/            # Database utilities
│   ├── domain/              # Domain models
│   ├── error-handling/      # Error handling utilities
│   ├── testing/             # Testing utilities
│   ├── ui-components/       # UI components
│   └── utils/               # Shared utilities
│
├── scripts/                 # Utility scripts
│   ├── build/               # Build scripts
│   ├── deploy/              # Deployment scripts
│   ├── test/                # Test scripts
│   └── utils/               # Utility scripts
│
└── tests/                   # Top-level tests
    ├── e2e/                 # End-to-end tests
    ├── integration/         # Integration tests
    └── performance/         # Performance tests
```

## Naming Conventions

- **Directories**: Use kebab-case for directories (`error-handling/`, `ui-components/`)
- **Files**:
  - JavaScript/TypeScript: Use camelCase for files (`redisClient.ts`, `errorHandler.js`)
  - React components: Use PascalCase for component files (`Button.tsx`, `ErrorBoundary.tsx`)
  - Python files: Use snake_case for files (`redis_client.py`, `error_handler.py`)
- **Imports**: Use path aliases where supported for clean imports (`@/utils/format`)

## Packages

Shared packages in the `packages/` directory follow a standard structure:

```
packages/package-name/
├── src/                  # Source code
│   ├── index.ts          # Main export file
│   └── components/       # Components (if applicable)
├── tests/                # Package tests
├── package.json          # Package metadata
└── README.md             # Package documentation
```

## Applications

Applications in the `apps/` directory follow this structure:

```
apps/service-name/
├── src/                  # Source code
│   ├── api/              # API endpoints
│   ├── config/           # Service-specific config
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   └── utils/            # Utilities
├── tests/                # Tests
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── package.json          # Dependencies (JS/TS)
├── requirements.txt      # Dependencies (Python)
└── README.md             # Service documentation
```

## Configuration

Configuration follows a hierarchical structure:

1. Default configurations in `config/`
2. Service-specific configurations in `config/app/<service>/`
3. Environment-specific configurations in `config/environments/<env>/`
4. Local overrides via `.env` files

## Docker

Docker configurations follow these conventions:

1. Use multi-stage builds for efficient images
2. Standardized base images for consistency
3. Non-root users for security
4. Proper health checks for all services

## Kubernetes

Kubernetes configurations follow these conventions:

1. Resource limits and requests for all deployments
2. Health checks for all services
3. Standardized labels and annotations
4. Environment-specific manifests in separate directories