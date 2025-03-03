# Migration Reference Guide

This document serves as a reference to the original migration files that were consolidated into the new Supabase migration system.

## Consolidated Migration Status

All migrations have been consolidated into a single baseline migration:

- **Baseline Migration**: `supabase/migrations/20250303183957_baseline/`
- **Applied On**: March 3, 2025

## Original Migration Files Reference

The original migration files have been archived in the `archived_migrations` directory for historical reference. These files should not be used for new migrations.

### Alembic Migrations (Python)

Original location: `./apps/api/database/migrations/versions/`
Archived location: `archived_migrations/alembic/`

Notable migrations:
- `add_api_keys_table.py`
- `add_api_key_scopes.py`

### Prisma Migrations

Original location: `./apps/api/db/migrations/`
Archived location: `archived_migrations/prisma/`

Notable migrations:
- `2023_12_01_000800_create_mailydocs_tables.sql`

### SQL Migrations

Original location: `./packages/database/migrations/`
Archived location: `archived_migrations/sql/`

Notable migrations:
- `001_add_indexes.sql`
- `002_create_consent_tables.sql`
- `003_create_plugin_tables.sql`
- `004_optimize_schema.sql`

## Migration Dependencies Removed

As part of the consolidation, the following dependencies were removed:

1. **Alembic**
   - Removed from `requirements.txt`
   - No longer needed for database migrations

2. **Prisma**
   - Removed migration commands from package.json scripts
   - Prisma client can still be used for database access, but migrations are now handled by Supabase

## Future Migrations

All future migrations should be created using the new migration system:

```bash
./scripts/create-migration.sh "Description of your migration"
```

This will create a properly structured migration in the `supabase/migrations` directory.

## Applying Migrations

To apply migrations:

```bash
./scripts/db-migration.sh development migrate
```

For production:

```bash
./scripts/db-migration.sh production migrate
```

## Rollback Process

To roll back migrations:

```bash
./scripts/db-migration.sh development rollback
```

To roll back to a specific migration:

```bash
./scripts/db-migration.sh development rollback 20250303183957_baseline
``` 