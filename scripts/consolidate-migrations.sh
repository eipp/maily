#!/bin/bash
# Migration Consolidation Script for Maily
# This script consolidates all migration systems into a single Supabase-based system

set -e

# Default values
ENVIRONMENT="${1:-development}"
LOG_DIR="deployment_logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/migration_consolidation_${TIMESTAMP}.log"
SNAPSHOT_DIR="database/snapshots"
SUPABASE_MIGRATIONS_DIR="supabase/migrations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log and directories if they don't exist
mkdir -p $LOG_DIR
mkdir -p $SUPABASE_MIGRATIONS_DIR

# Display banner
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}                MAILY MIGRATION CONSOLIDATION${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo ""

# Log start
echo "====================================================================" | tee -a $LOG_FILE
echo "Starting Maily Migration Consolidation" | tee -a $LOG_FILE
echo "Environment: ${ENVIRONMENT}" | tee -a $LOG_FILE
echo "Timestamp: $(date)" | tee -a $LOG_FILE
echo "====================================================================" | tee -a $LOG_FILE

# Function to display step information
step() {
  echo -e "${BLUE}-> $1${NC}" | tee -a $LOG_FILE
}

# Function to display success messages
success() {
  echo -e "${GREEN}✓ $1${NC}" | tee -a $LOG_FILE
}

# Function to display warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}" | tee -a $LOG_FILE
}

# Function to display error messages and exit
error() {
  echo -e "${RED}ERROR: $1${NC}" | tee -a $LOG_FILE
  exit 1
}

# Function to run a command with logging
run_command() {
  local cmd="$1"
  local error_msg="${2:-Command failed}"

  echo "$ $cmd" | tee -a $LOG_FILE
  if eval "$cmd" >> $LOG_FILE 2>&1; then
    return 0
  else
    local exit_code=$?
    error "${error_msg} (Exit code: ${exit_code})"
    return $exit_code
  fi
}

# Check if Supabase CLI is installed
step "Checking Supabase CLI"
if ! command -v supabase &> /dev/null; then
  step "Installing Supabase CLI"
  run_command "npm install -g supabase" "Failed to install Supabase CLI"
  success "Supabase CLI installed"
else
  success "Supabase CLI already installed"
fi

# Create Supabase project if it doesn't exist
step "Checking Supabase project"
if [ ! -f "supabase/config.toml" ]; then
  step "Initializing Supabase project"
  mkdir -p supabase
  run_command "supabase init" "Failed to initialize Supabase project"
  success "Supabase project initialized"
else
  success "Supabase project already exists"
fi

# Find latest schema snapshot
step "Finding latest schema snapshot"
LATEST_SNAPSHOT=$(find "${SNAPSHOT_DIR}" -name "schema_snapshot_*.sql" | sort -r | head -n 1)

if [ -z "$LATEST_SNAPSHOT" ]; then
  warning "No schema snapshot found. Creating one now..."
  run_command "./scripts/schema-snapshot.sh ${ENVIRONMENT}" "Failed to create schema snapshot"
  LATEST_SNAPSHOT=$(find "${SNAPSHOT_DIR}" -name "schema_snapshot_*.sql" | sort -r | head -n 1)
  
  if [ -z "$LATEST_SNAPSHOT" ]; then
    error "Failed to create schema snapshot"
  fi
fi

success "Found schema snapshot: ${LATEST_SNAPSHOT}"

# Create baseline migration
step "Creating baseline migration from snapshot"
BASELINE_TIMESTAMP=$(date +%Y%m%d%H%M%S)
BASELINE_MIGRATION_DIR="${SUPABASE_MIGRATIONS_DIR}/${BASELINE_TIMESTAMP}_baseline"
mkdir -p "${BASELINE_MIGRATION_DIR}"

# Copy snapshot to baseline up migration
cp "${LATEST_SNAPSHOT}" "${BASELINE_MIGRATION_DIR}/migration.sql"

# Create baseline down migration (for rollback)
cat << EOF > "${BASELINE_MIGRATION_DIR}/down.sql"
-- Baseline migration rollback
-- Warning: This will drop all tables and data!
-- Only use in development or when you have backups

-- Get all tables in public schema
DO \$\$
DECLARE
  r RECORD;
BEGIN
  FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
    EXECUTE 'DROP TABLE IF EXISTS "' || r.tablename || '" CASCADE';
  END LOOP;
END \$\$;
EOF

success "Created baseline migration: ${BASELINE_MIGRATION_DIR}/migration.sql"

# Create migration metadata
step "Creating migration metadata file"
cat << EOF > "${BASELINE_MIGRATION_DIR}/metadata.json"
{
  "version": "1",
  "description": "Baseline migration from consolidated schema snapshot",
  "source": "consolidated",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "environment": "${ENVIRONMENT}",
  "consolidated": true,
  "original_systems": [
    "SQL Migrations (packages/database/migrations/*.sql)",
    "Alembic Migrations (apps/api/database/migrations/versions/*.py)",
    "Prisma Migrations (packages/db)",
    "Supabase Migrations (scripts/db-migration.sh)"
  ]
}
EOF

success "Created migration metadata file"

# Update migration documentation
step "Updating migration documentation"
mkdir -p docs/migrations

cat << EOF > docs/migrations/MIGRATION-CONSOLIDATION.md
# Migration Consolidation

## Overview

This document describes the consolidation of multiple migration systems into a single Supabase-based migration system.

## Previous Migration Systems

Prior to consolidation, the project used multiple migration systems:

1. **SQL Migrations** (packages/database/migrations/*.sql)
2. **Alembic Migrations** (apps/api/database/migrations/versions/*.py)
3. **Prisma Migrations** (packages/db)
4. **Supabase Migrations** (scripts/db-migration.sh)

## Consolidated Migration System

As of $(date), all migrations have been consolidated into a single Supabase-based system:

- **Baseline Migration**: ${BASELINE_MIGRATION_DIR}/migration.sql
- **Migration Script**: scripts/db-migration.sh

## Migration Process

To perform migrations:

\`\`\`bash
# For development
./scripts/db-migration.sh development migrate

# For production
./scripts/db-migration.sh production migrate

# For rollback
./scripts/db-migration.sh production rollback
\`\`\`

## Additional Resources

- Schema snapshots are stored in: ${SNAPSHOT_DIR}
- Supabase migrations are stored in: ${SUPABASE_MIGRATIONS_DIR}
EOF

success "Updated migration documentation"

# Output success
echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}                 MIGRATION CONSOLIDATION COMPLETED${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo -e "${GREEN}=====================================================================${NC}"

echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Review the baseline migration in ${BASELINE_MIGRATION_DIR}/migration.sql"
echo "2. Review the migration documentation in docs/migrations/MIGRATION-CONSOLIDATION.md"
echo "3. Use the consolidated migration system going forward:"
echo "   ./scripts/db-migration.sh ${ENVIRONMENT} migrate"

exit 0 