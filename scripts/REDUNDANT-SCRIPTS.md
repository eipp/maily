# Redundant Scripts

This document lists the scripts that have been made redundant by the consolidation effort. These scripts have been superseded by more comprehensive and better-organized alternatives.

## Security Scanning Scripts

| Redundant Script | Replaced By | Reason |
|------------------|-------------|--------|
| `scripts/automated-security-scan.sh` | `scripts/security/security-scan.sh` | Consolidated into a more comprehensive security scanning tool with support for multiple engines and better reporting. |
| `scripts/security-scanning.sh` | `scripts/security/security-scan.sh` | Functionality merged into the consolidated security scanner to reduce code duplication and standardize interfaces. |

## Load Testing Scripts

| Redundant Script | Replaced By | Reason |
|------------------|-------------|--------|
| `scripts/load-testing.sh` | `scripts/testing/load-testing/consolidated-load-test.sh` | Consolidated into a unified load testing framework that supports multiple engines and provides a consistent interface. |
| `scripts/load_test.py` | `scripts/testing/load-testing/consolidated-load-test.sh` | Python load testing functionality has been integrated into the consolidated script with improved parameterization. |
| `scripts/performance/test_blockchain_performance.js` | `scripts/testing/load-testing/consolidated-load-test.sh` | Specific blockchain performance testing is now handled by the consolidated load testing script with appropriate parameters. |
| `scripts/performance/locustfile.py` | `scripts/testing/load-testing/consolidated-load-test.sh` | Locust configuration has been integrated into the consolidated load testing framework. |
| `scripts/performance/load_test.py` | `scripts/testing/load-testing/consolidated-load-test.sh` | Duplicate functionality now provided by the consolidated load testing script. |
| `scripts/performance/test_canvas_performance.js` | `scripts/testing/load-testing/consolidated-load-test.sh` | Canvas-specific performance testing now available as a test type in the consolidated script. |

## Database Migration Scripts

| Redundant Script | Replaced By | Reason |
|------------------|-------------|--------|
| `scripts/db-migration.sh` | `scripts/database/manage-migrations.sh` | Superseded by the comprehensive database migration manager with additional functionality. |
| `scripts/check-migrations.sh` | `scripts/database/manage-migrations.sh` | Migration checking is now a feature of the consolidated migration manager. |
| `scripts/schema-snapshot.sh` | `scripts/database/manage-migrations.sh` | Schema snapshot functionality is now integrated into the migration manager. |
| `scripts/create-migration.sh` | `scripts/database/manage-migrations.sh` | Migration creation is now part of the consolidated tool with improved templating. |
| `scripts/validate-migrations.js` | `scripts/database/manage-migrations.sh` | Migration validation is now performed by the consolidated migration manager. |
| `scripts/consolidate-migrations.sh` | `scripts/database/manage-migrations.sh` | Migration consolidation is now available as an operation in the migration manager. |

## Unified CLI Tool Migration

| Redundant Script | Replaced By | Reason |
|------------------|-------------|--------|
| `scripts/core/maily-deploy.sh` | `mailyctl.py phased-deploy` | Consolidated into the unified CLI tool with enhanced functionality and better parameter handling. |
| `scripts/core/deploy-phases/phase1-staging.sh` | `mailyctl.py phased-deploy` | Integrated into the phased deployment command of the unified CLI tool. |
| `scripts/core/deploy-phases/phase2-prod-initial.sh` | `mailyctl.py phased-deploy` | Integrated into the phased deployment command with consistent parameter handling. |
| `scripts/core/deploy-phases/phase3-prod-full.sh` | `mailyctl.py phased-deploy` | Integrated into the phased deployment command with improved error handling. |
| `vault/scripts/auto-rotate-secrets.py` | `mailyctl.py secrets rotate` | Secret rotation functionality consolidated into the unified CLI tool. |
| `system/verifiers/service-mesh-verifier.js` | `mailyctl.py verify-mesh` | Service mesh verification functionality moved to the Python-based unified CLI tool. |

## Safe Cleanup Process

To safely clean up these redundant scripts:

1. Run the reference update utility to ensure all script references in other files have been updated:
   ```
   scripts/update-references.sh --mode auto
   ```

2. Verify that the new consolidated scripts function correctly by running tests.

3. Use the cleanup script to safely remove redundant scripts (making backups first):
   ```
   scripts/cleanup-redundant-scripts.sh --mode backup-only  # Just create backups
   scripts/cleanup-redundant-scripts.sh --mode delete       # Backup and delete
   ```

In case of issues, backups are stored in a timestamped directory under `scripts/backup_before_cleanup_TIMESTAMP/` and can be used to restore files if needed.
