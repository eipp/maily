# Script Consolidation Plan

## Overview

This document outlines the comprehensive plan for reorganizing and consolidating scripts in the Maily repository. The goal is to improve maintainability, reduce redundancy, and create a clear organization structure for all deployment and operational scripts.

## New Directory Structure

```
scripts/
├── core/                   # Core deployment scripts
│   ├── maily-deploy.sh
│   ├── deployment-validator.sh
│   ├── config-collector.sh
│   ├── update-image-tags.sh
│   ├── phase1-staging.sh
│   ├── phase2-prod-initial.sh
│   └── phase3-prod-full.sh
│
├── testing/                # Testing frameworks
│   ├── smoke-test.js
│   ├── enhanced-smoke-test.js
│   ├── e2e-staging-test.js
│   ├── run_tests.sh
│   ├── run-chaos-tests.sh
│   ├── test-ai-ml.sh
│   └── load-testing/       # Load testing utilities
│       ├── consolidated-load-test.sh
│       ├── k6-load-test.js
│       ├── locustfile.py
│       ├── load_test.py
│       ├── stress_test.py
│       └── test_blockchain_performance.js
│
├── security/               # Security scanning tools
│   ├── security-scan.sh    # Consolidated scanning tool
│   ├── secret-rotation.sh
│   ├── create-k8s-secrets.sh
│   ├── setup-auth-security.sh
│   ├── zap-scan.sh
│   ├── enhance_blockchain_security.py
│   └── enhance_security_monitoring.py
│
├── infrastructure/         # Infrastructure setup
│   ├── deploy-eks-cluster.sh
│   ├── setup-production-rds.sh
│   ├── setup-redis-cluster.sh
│   ├── deploy-cloudflare-waf.sh
│   ├── setup-devops-infrastructure.sh
│   ├── setup-production-environment.sh
│   ├── setup-datadog-monitoring.sh
│   ├── configure-dns.sh
│   ├── configure-ssl-tls.sh
│   └── automated-certificate-management.sh
│
├── database/               # Database operations
│   ├── manage-migrations.sh # Consolidated migration tool
│   ├── db-migration.sh
│   ├── check-migrations.sh
│   ├── validate-migrations.js
│   ├── schema-snapshot.sh
│   ├── create-migration.sh
│   ├── configure-database-backups.sh
│   └── consolidate-migrations.sh
│
├── docs/                   # Documentation generators
│   ├── docs-automation.js
│   ├── generate-api-docs.js
│   ├── generate-inline-docs.js
│   ├── verify-doc-links.js
│   ├── cleanup-docs.js
│   ├── adr.js
│   └── adr-template.md
│
├── utils/                  # Utility scripts
│   ├── check-dependencies.js
│   ├── check-critical-metrics.sh
│   ├── automated-rollback.sh
│   ├── generate-encryption-key.js
│   ├── generate-icons.js
│   ├── update-dependencies.sh
│   ├── update-missing-dependencies.js
│   ├── docker-compose-env.sh
│   ├── source-env.sh
│   ├── get-refresh-token.js
│   ├── setup-dev-environment.sh
│   ├── install-core-deps.js
│   ├── install-shadcn.sh
│   └── verify-all-scripts.sh
│
├── migrate-scripts.sh     # Migration utility that moves files to new location
├── update-references.sh   # Utility to update references in other files
├── cleanup-redundant-scripts.sh # Script to safely remove redundant scripts
├── REDUNDANT-SCRIPTS.md   # List of scripts made redundant
└── CONSOLIDATION-PLAN.md  # This file
```

## Script Consolidations

The following scripts have been consolidated into more comprehensive utilities:

### Security Scanning
| Original Scripts | Consolidated Into |
|------------------|------------------|
| scripts/automated-security-scan.sh | scripts/security/security-scan.sh |
| scripts/security-scanning.sh | scripts/security/security-scan.sh |

The consolidated script provides a comprehensive security scanning utility with:
- Multiple scanning engines (ZAP, Trivy, etc.)
- Configurable scan depth and targets
- Improved reporting capabilities
- Integration with CI/CD pipelines

### Load Testing
| Original Scripts | Consolidated Into |
|------------------|------------------|
| scripts/load-testing.sh | scripts/testing/load-testing/consolidated-load-test.sh |
| scripts/load_test.py | scripts/testing/load-testing/consolidated-load-test.sh |
| scripts/performance/* | scripts/testing/load-testing/consolidated-load-test.sh |

The consolidated load testing script provides:
- Support for multiple testing engines (k6, Locust, Artillery, etc.)
- Consistent interface for all test types
- Configurable test parameters (duration, users, etc.)
- Multiple output formats

### Database Migrations
| Original Scripts | Consolidated Into |
|------------------|------------------|
| scripts/db-migration.sh | scripts/database/manage-migrations.sh |
| scripts/check-migrations.sh | scripts/database/manage-migrations.sh |
| scripts/schema-snapshot.sh | scripts/database/manage-migrations.sh |
| scripts/create-migration.sh | scripts/database/manage-migrations.sh |
| scripts/validate-migrations.js | scripts/database/manage-migrations.sh |
| scripts/consolidate-migrations.sh | scripts/database/manage-migrations.sh |

The consolidated migration manager provides:
- A single interface for all database migration tasks
- Support for multiple environments (development, staging, production)
- Migration validation functionality
- Schema snapshot and backup capabilities
- Rollback functionality
- Prisma integration

## Implementation Plan

The implementation of this consolidation plan will proceed in the following phases:

1. **Directory Structure Creation** - Create the new directory structure
2. **Script Migration** - Move existing scripts to their new locations
3. **Tool Development** - Develop the consolidated tools
4. **Update References** - Update references to the moved scripts in other files
5. **Testing** - Test all scripts in their new locations
6. **Cleanup** - Remove redundant scripts after verification

## Consolidation Benefits

This consolidation brings several benefits:

1. **Improved Organization** - Clear separation of responsibilities
2. **Reduced Redundancy** - Eliminates duplicate code and functionality
3. **Enhanced Capabilities** - Consolidated scripts provide more comprehensive functionality
4. **Better Documentation** - Clearer structure makes it easier to understand available scripts
5. **Easier Maintenance** - Centralized functionality makes updates and fixes easier
6. **Standardized Interfaces** - Consistent interfaces across scripts
