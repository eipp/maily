# Migration Consolidation Process

## Summary

This document outlines the one-time process that was performed to consolidate multiple migration systems (Prisma, Alembic, and SQL scripts) into a single Supabase-based migration system for Maily.

## Consolidation Steps Completed

1. **Schema Snapshot Creation**
   - Used `scripts/schema-snapshot.sh` to create a point-in-time snapshot of the current schema
   - This snapshot became our baseline migration (`20250303183957_baseline`)

2. **Migration History Preservation**
   - Created a `migration_history` table to track all applied migrations
   - Populated it with metadata from the previous migration systems

3. **Reorganization of Migration Files**
   - Consolidated all migrations into the Supabase format in `supabase/migrations/`
   - Archived old migration systems in `archived_migrations/`

4. **Workflow Simplification**
   - Created utility scripts for common migration tasks
   - Set up GitHub Actions workflow for automated migration validation and deployment

## Current Migration Structure

The consolidated migration system now follows this structure:

```
supabase/migrations/
  ├── 20250303183957_baseline/        # Baseline migration containing all tables
  │   ├── migration.sql               # Full schema creation
  │   ├── down.sql                    # Schema teardown
  │   └── metadata.json               # Migration metadata
  └── [subsequent migrations...]      # Additional migrations after baseline
```

## Key Tables Included in Baseline

The baseline migration (`20250303183957_baseline`) includes these core tables:

- `migration_history` - Tracks applied migrations
- `users` - User accounts
- `accounts` - Authentication accounts (OAuth, etc.)
- `sessions` - User sessions
- `api_keys` - API keys for external access
- `api_key_scopes` - Scopes for API keys
- `templates` - Email templates
- `consent_purposes` - User consent categories
- `user_consents` - User consent records
- `plugins` - Available system plugins
- `user_plugins` - User plugin associations

## New Migration System Benefits

- **Single Source of Truth**: All migrations now follow one consistent format
- **Full Rollback Support**: Each migration has both up and down SQL
- **Better Metadata**: Each migration includes descriptive information
- **Simplified Workflow**: Standard scripts for all migration operations
- **Automated Testing**: GitHub Actions validates migrations before deployment
- **Improved Deployment**: Streamlined deployment to all environments

## Ongoing Maintenance

1. **Creating New Migrations**
   ```bash
   ./scripts/create-migration.sh "Description of the change"
   ```

2. **Applying Migrations**
   ```bash
   ./scripts/db-migration.sh [environment] migrate
   ```

3. **Rolling Back**
   ```bash
   ./scripts/db-migration.sh [environment] rollback
   ```

4. **Checking Migration Status**
   ```bash
   ./scripts/check-migrations.sh [environment]
   ```

## Background

### Previous Migration Systems

Prior to consolidation, Maily used multiple migration systems:

1. **Prisma Migrations**: Used for the core schema and developer local environments
2. **Alembic**: Used for Python-driven migrations
3. **Raw SQL Scripts**: Ad-hoc migrations for specific features

This created several challenges:
- Inconsistent versioning between systems
- Difficulty tracking what had been applied
- Conflicts between migrations
- No comprehensive rollback support
- Complex deployment processes

### Consolidation Rationale

The decision to consolidate was driven by:
- Need for consistent versioning across all environments
- Desire for simpler, automated deployments
- Requirement for comprehensive rollback support
- Better tracking of migration history
- Simplified developer workflow

### Implementation Process

The consolidation was implemented using the following steps:

1. **Evaluation Phase**: Assessed existing migrations and their interdependencies
2. **Tool Creation**: Developed specialized scripts for migration management
3. **Schema Snapshot**: Created a point-in-time snapshot of the complete schema
4. **Migration History**: Established a system for tracking migrations
5. **GitHub Actions**: Set up automated validation and deployment
6. **Documentation**: Updated all documentation to reflect the new system

This process was completed successfully on March 3, 2025, establishing a unified migration system that will serve as the foundation for all future schema changes.

## Consolidation Strategy Implementation

The migration consolidation was implemented following this strategy:

### 1. Schema Snapshot

Created a baseline schema snapshot representing the current state of the database:
- Used `pg_dump` to capture the complete schema
- Excluded system tables and unnecessary objects
- Formatted the output as executable SQL

### 2. Migration History Table

Implemented a comprehensive migration history table:
```sql
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    migration_source TEXT DEFAULT 'consolidated',
    migration_description TEXT
);
```

### 3. Utility Scripts Development

Created the following utility scripts:
- `schema-snapshot.sh`: Creates schema snapshots
- `consolidate-migrations.sh`: Performs the consolidation process
- `db-migration.sh`: Applies or rolls back migrations
- `create-migration.sh`: Creates new migrations
- `check-migrations.sh`: Checks migration status
- `source-env.sh`: Sources environment variables

### 4. GitHub Actions Workflow

Implemented automated CI/CD for migrations:
- Validates migrations on pull requests
- Deploys migrations when merging to main
- Allows manual deployment via workflow dispatch
- Includes notifications for success/failure

### 5. Documentation Updates

Updated project documentation:
- Created this migration consolidation guide
- Updated the main migration README
- Added inline comments to all scripts

## Archiving Previous Migration Systems

All previous migration systems have been archived:
- Moved to `archived_migrations/` directory
- Added documentation about the archival process
- Retained for historical reference only

## Future Considerations

Moving forward, all schema changes will follow this workflow:
1. Create a new migration using `create-migration.sh`
2. Develop and test the migration locally
3. Submit a pull request with the migration
4. The GitHub Actions workflow will validate the migration
5. When merged, the migration will be automatically applied to development
6. Production deployments are performed manually via workflow dispatch

## Migration Scripts Reference

### schema-snapshot.sh

Creates a point-in-time snapshot of the database schema:

```bash
# Usage
./scripts/schema-snapshot.sh [environment]
```

Key features:
- Captures complete database schema
- Excludes data and system tables
- Creates a properly formatted migration
- Records snapshot in migration history

### consolidate-migrations.sh

Consolidates multiple migration systems into a single system:

```bash
# Usage
./scripts/consolidate-migrations.sh [environment]
```

Key features:
- Creates baseline migration
- Archives old migration systems
- Sets up migration history
- Generates metadata

### db-migration.sh

Manages database migrations (apply, rollback, reset):

```bash
# Apply migrations
./scripts/db-migration.sh [environment] migrate

# Rollback most recent migration
./scripts/db-migration.sh [environment] rollback

# Rollback to specific migration
./scripts/db-migration.sh [environment] rollback [migration_name]

# Reset database (caution: destroys data)
./scripts/db-migration.sh [environment] reset
```

Key features:
- Creates backups before migrations
- Checks migration history
- Handles both up and down migrations
- Manages migration metadata

### create-migration.sh

Creates a new migration with up and down SQL files:

```bash
# Usage
./scripts/create-migration.sh "Description of the migration"
```

Key features:
- Generates timestamped migration directory
- Creates migration.sql (up), down.sql, and metadata.json
- Provides templates for common operations
- Includes helpful comments

### check-migrations.sh

Checks if migrations need to be applied:

```bash
# Usage
./scripts/check-migrations.sh [environment]
```

Key features:
- Compares available migrations with applied migrations
- Returns non-zero exit code if migrations are needed
- Provides detailed output of pending migrations
- Used in CI/CD workflows

### source-env.sh

Sources environment variables from .env files:

```bash
# Usage (called by other scripts)
source ./scripts/source-env.sh [environment]
```

Key features:
- Loads environment-specific variables
- Handles various .env file formats
- Validates environment configuration
- Skips comments and empty lines

## Migration Format Reference

### Directory Structure

Each migration is stored in its own timestamped directory with a descriptive name:

```
20250303184157_add-user-preferences-table/
├── migration.sql   # Up migration (applied during migration)
├── down.sql        # Down migration (applied during rollback)
└── metadata.json   # Migration metadata
```

### Migration File (migration.sql)

The up migration file contains SQL to apply the changes:

```sql
-- Migration: 20250303184157_add-user-preferences-table
-- Description: Adds user preferences table to store user settings
-- Created: 2025-03-03T18:41:57Z

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key TEXT NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- Add indexes
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Record migration in history
INSERT INTO migration_history (migration_name, migration_description)
VALUES ('20250303184157_add-user-preferences-table', 'Adds user preferences table to store user settings');
```

### Rollback File (down.sql)

The down migration file contains SQL to revert the changes:

```sql
-- Down Migration: 20250303184157_add-user-preferences-table
-- Description: Removes user preferences table
-- Created: 2025-03-03T18:41:57Z

-- Drop table
DROP TABLE IF EXISTS user_preferences;

-- Remove from migration history
DELETE FROM migration_history 
WHERE migration_name = '20250303184157_add-user-preferences-table';
```

### Metadata File (metadata.json)

The metadata file contains information about the migration:

```json
{
  "id": "20250303184157_add-user-preferences-table",
  "description": "Adds user preferences table to store user settings",
  "created_at": "2025-03-03T18:41:57Z",
  "author": "development",
  "type": "feature",
  "dependencies": ["20250303183957_baseline"]
}
```

### Migration History Table

Migrations are tracked in the `migration_history` table:

```sql
SELECT * FROM migration_history;
```

Example output:
```
id | migration_name                         | applied_at           | migration_source | migration_description
---+----------------------------------------+----------------------+------------------+-------------------------------------------
1  | 20250303183957_baseline                | 2025-03-03 18:39:57 | consolidated     | Baseline schema snapshot
2  | 20250303184157_add-user-preferences-table | 2025-03-03 18:41:57 | consolidated     | Adds user preferences table to store user settings
```

## GitHub Actions CI/CD Integration

The GitHub Actions workflow in `.github/workflows/migrations.yml` automates the database migration process. It includes:

- **Validation Job**: Runs on pull requests to ensure migrations are valid
- **Deployment Job**: Runs on merges to main and manual dispatch events
- **Manual Trigger**: Allows selecting the target environment (development, staging, production)

The workflow provides:
- Consistent validation across environments
- Automated deployment to development on merge
- Manual control for production deployments
- Notifications on success or failure 