#!/bin/bash
# Migration Creation Script for Maily
# This script creates a new migration for the consolidated migration system

set -e

# Check if description is provided
if [ -z "$1" ]; then
  echo "Error: Migration description is required"
  echo "Usage: $0 <description>"
  echo "Example: $0 'add-user-preferences-column'"
  exit 1
fi

# Variables
DESCRIPTION=$(echo "$1" | tr ' ' '-' | tr -d "'" | tr -d '"' | tr '[:upper:]' '[:lower:]')
TIMESTAMP=$(date +%Y%m%d%H%M%S)
MIGRATION_DIR="supabase/migrations/${TIMESTAMP}_${DESCRIPTION}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create migration directory
mkdir -p $MIGRATION_DIR

# Create migration file
cat << EOF > ${MIGRATION_DIR}/migration.sql
-- Migration: ${DESCRIPTION}
-- Created at: $(date)
-- Description: $1

-- Write your migration SQL here

-- Update migration history table
INSERT INTO migration_history (migration_name, migration_description)
VALUES ('${TIMESTAMP}_${DESCRIPTION}', '$1')
ON CONFLICT (migration_name) DO NOTHING;
EOF

# Create down migration file for rollbacks
cat << EOF > ${MIGRATION_DIR}/down.sql
-- Rollback for migration: ${DESCRIPTION}
-- Created at: $(date)
-- Description: $1

-- Write your rollback SQL here

-- Remove from migration history table
DELETE FROM migration_history WHERE migration_name = '${TIMESTAMP}_${DESCRIPTION}';
EOF

# Create metadata file
cat << EOF > ${MIGRATION_DIR}/metadata.json
{
  "version": "1",
  "description": "$1",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "source": "manual",
  "author": "$(whoami)"
}
EOF

echo -e "${GREEN}Migration created successfully:${NC}"
echo "- ${MIGRATION_DIR}/migration.sql (up migration)"
echo "- ${MIGRATION_DIR}/down.sql (down migration)"
echo "- ${MIGRATION_DIR}/metadata.json (metadata)"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Edit ${MIGRATION_DIR}/migration.sql to add your migration SQL"
echo "2. Edit ${MIGRATION_DIR}/down.sql to add rollback SQL"
echo "3. Apply migration with: ./scripts/db-migration.sh development migrate"

exit 0 