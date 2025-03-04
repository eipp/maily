# Maily Database Migration System

## Overview

The Maily database migration system is built on Supabase's migration tools, providing a versioned approach to database schema management with full rollback support. All previous migration systems (Prisma, Alembic, and SQL scripts) have been consolidated into this single system.

## Core Scripts

| Script | Description |
|--------|-------------|
| `scripts/database/manage-migrations.sh` | Consolidated migration script for creating, applying, and checking migrations |

## Directory Structure

```
supabase/migrations/
  ├── 20250303183957_baseline/        # Consolidated baseline migration
  │   ├── migration.sql               # Up migration
  │   ├── down.sql                    # Down migration
  │   └── metadata.json               # Migration metadata
  └── 20250303184157_add-user-preferences-table/  # Example feature migration
      ├── migration.sql
      ├── down.sql
      └── metadata.json
```

## Common Commands

### Creating a New Migration

```bash
./scripts/database/manage-migrations.sh create "Description of the change"
```

This creates a properly structured migration with up/down SQL files and metadata.

### Applying Migrations

```bash
./scripts/database/manage-migrations.sh development migrate
```

For production:

```bash
./scripts/database/manage-migrations.sh production migrate
```

### Rolling Back a Migration

```bash
./scripts/database/manage-migrations.sh development rollback
```

To roll back to a specific migration:

```bash
./scripts/database/manage-migrations.sh development rollback 20250303183957_baseline
```

### Checking Migration Status

```bash
./scripts/database/manage-migrations.sh development status
```

## Automated Workflows

The GitHub Actions workflow in `.github/workflows/migrations.yml` automates:
- Validation of migrations on pull requests
- Deployment of migrations when merging to main
- Manual deployment via workflow dispatch

## Archived Migration Systems

Previous migration systems have been archived in the `archived_migrations/` directory:
- Alembic migrations: `archived_migrations/alembic/`
- Prisma migrations: `archived_migrations/prisma/`
- SQL migrations: `archived_migrations/sql/`

These are kept for reference only and should not be used.

## Migration History Table

```sql
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    migration_source TEXT DEFAULT 'consolidated',
    migration_description TEXT
);
```

## Troubleshooting

### Failed Migrations

If a migration fails:
1. Check the error message in `deployment_logs/`
2. Fix the issue in the migration file
3. Rerun the migration command

### Database Connection Issues

Ensure your DATABASE_URL is set correctly in your .env file:

```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
``` 