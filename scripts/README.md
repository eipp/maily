# Maily Scripts

This directory contains scripts for deploying, testing, monitoring, and managing the Maily application.

## Script Organization

Scripts are organized into the following categories:

- **Core** (`scripts/core/`): Core deployment scripts
- **Testing** (`scripts/testing/`): Testing frameworks and utilities
- **Security** (`scripts/security/`): Security scanning and management tools
- **Infrastructure** (`scripts/infrastructure/`): Infrastructure setup and management
- **Database** (`scripts/database/`): Database operations and migrations
- **Docs** (`scripts/docs/`): Documentation generation tools
- **Utils** (`scripts/utils/`): Utility scripts for various tasks

## Consolidated Scripts

The following scripts provide comprehensive functionality by consolidating multiple smaller scripts:

| Script | Description |
|--------|-------------|
| `scripts/security/security-scan.sh` | Comprehensive security scanning utility supporting multiple scan engines |
| `scripts/testing/load-testing/consolidated-load-test.sh` | Unified load testing framework with multiple engine support |
| `scripts/database/manage-migrations.sh` | Complete database migration management system |

## Utilities

| Script | Description |
|--------|-------------|
| `scripts/update-references.sh` | Updates references to moved scripts in other files |
| `scripts/cleanup-redundant-scripts.sh` | Safely removes redundant scripts with backup options |
| `scripts/verify-consolidation.sh` | Verifies the success of the script consolidation |

## Documentation

- **[CONSOLIDATION-PLAN.md](./CONSOLIDATION-PLAN.md)**: Detailed plan for script consolidation
- **[REDUNDANT-SCRIPTS.md](./REDUNDANT-SCRIPTS.md)**: List of scripts made redundant by consolidation

## Usage Examples

### Security Scanning

```bash
# Run a complete security scan
scripts/security/security-scan.sh --scan-type full

# Run a quick scan of a specific component
scripts/security/security-scan.sh --scan-type quick --component api
```

### Load Testing

```bash
# Run a load test against the API with 100 users for 5 minutes
scripts/testing/load-testing/consolidated-load-test.sh --type api --users 100 --duration 5m

# Run a stress test using the k6 engine
scripts/testing/load-testing/consolidated-load-test.sh --type stress --engine k6
```

### Database Management

```bash
# Apply pending migrations
scripts/database/manage-migrations.sh --operation migrate --env development

# Create a new migration
scripts/database/manage-migrations.sh --operation create --name add_users_table

# Create a database backup
scripts/database/manage-migrations.sh --operation backup --env production
```

### Updating Script References

```bash
# Report mode - shows what would be updated
scripts/update-references.sh --target ./infrastructure

# Auto mode - updates references automatically
scripts/update-references.sh --mode auto
```

### Cleaning Up Redundant Scripts

```bash
# Dry run - shows what would be done
scripts/cleanup-redundant-scripts.sh

# Backup only - creates backups without deleting
scripts/cleanup-redundant-scripts.sh --mode backup-only

# Delete mode - creates backups and deletes redundant scripts
scripts/cleanup-redundant-scripts.sh --mode delete
```

### Verifying Consolidation

```bash
# Verify the success of the script consolidation
scripts/verify-consolidation.sh
