#!/bin/bash
# migrate-database.sh - Database migration script for Maily environments
# Usage: ./migrate-database.sh <source_env> <target_env> [options]
# source_env: Source environment (e.g., staging)
# target_env: Target environment (e.g., production)
# Options:
#   --dry-run: Only show what would be done, don't execute
#   --schema-only: Migrate schema without data
#   --with-seed-data: Include seed data in migration
#   --backup: Create a backup before migration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Input validation
if [ "$#" -lt 2 ]; then
    echo -e "${RED}Error: Insufficient arguments${NC}"
    echo -e "Usage: ./migrate-database.sh <source_env> <target_env> [options]"
    echo -e "Example: ./migrate-database.sh staging production --backup"
    exit 1
fi

SOURCE_ENV=$1
TARGET_ENV=$2
shift 2

# Default options
DRY_RUN=false
SCHEMA_ONLY=false
WITH_SEED_DATA=false
WITH_BACKUP=false

# Parse options
for opt in "$@"; do
    case $opt in
        --dry-run)
            DRY_RUN=true
            ;;
        --schema-only)
            SCHEMA_ONLY=true
            ;;
        --with-seed-data)
            WITH_SEED_DATA=true
            ;;
        --backup)
            WITH_BACKUP=true
            ;;
        *)
            echo -e "${RED}Unknown option: $opt${NC}"
            exit 1
            ;;
    esac
done

# Validate environments
VALID_ENVS=("development" "testing" "staging" "production")
if [[ ! " ${VALID_ENVS[*]} " =~ " ${SOURCE_ENV} " ]]; then
    echo -e "${RED}Invalid source environment: $SOURCE_ENV${NC}"
    echo -e "Valid environments: ${VALID_ENVS[*]}"
    exit 1
fi

if [[ ! " ${VALID_ENVS[*]} " =~ " ${TARGET_ENV} " ]]; then
    echo -e "${RED}Invalid target environment: $TARGET_ENV${NC}"
    echo -e "Valid environments: ${VALID_ENVS[*]}"
    exit 1
fi

# Prevent accidental migration to production without backup
if [[ "$TARGET_ENV" == "production" && "$WITH_BACKUP" == "false" && "$DRY_RUN" == "false" ]]; then
    echo -e "${RED}Error: Production migrations require --backup flag${NC}"
    echo -e "Run with --backup to create a backup before migration or use --dry-run to test"
    exit 1
fi

# Function for logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function for success messages
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function for warning messages
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function for error messages
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Get database connection details
get_db_url() {
    local env=$1
    local env_file="/Users/ivanpeychev/saas/maily/apps/api/.env.$env"
    
    if [ ! -f "$env_file" ]; then
        error "Environment file not found: $env_file"
    fi
    
    # Extract DATABASE_URL from environment file
    grep "DATABASE_URL" "$env_file" | cut -d '=' -f2-
}

SOURCE_DB_URL=$(get_db_url "$SOURCE_ENV")
TARGET_DB_URL=$(get_db_url "$TARGET_ENV")

if [ -z "$SOURCE_DB_URL" ] || [ -z "$TARGET_DB_URL" ]; then
    error "Failed to retrieve database URLs"
fi

# Extract DB names for logging (without exposing credentials)
SOURCE_DB_NAME=$(echo "$SOURCE_DB_URL" | sed -E 's/.*\/([^:]+)$/\1/')
TARGET_DB_NAME=$(echo "$TARGET_DB_URL" | sed -E 's/.*\/([^:]+)$/\1/')

log "Migration from $SOURCE_ENV ($SOURCE_DB_NAME) to $TARGET_ENV ($TARGET_DB_NAME)"
if [ "$DRY_RUN" = true ]; then
    log "DRY RUN MODE: No changes will be made"
fi

# Create backup if requested
create_backup() {
    local env=$1
    local db_url=$2
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="maily_${env}_backup_${timestamp}.sql"
    
    log "Creating backup of $env database..."
    if [ "$DRY_RUN" = true ]; then
        log "Would create backup to: $backup_file"
    else
        # Extract connection details for pg_dump
        local db_host=$(echo "$db_url" | sed -E 's/.*@([^:]+):.*/\1/')
        local db_port=$(echo "$db_url" | sed -E 's/.*:([0-9]+)\/.*/\1/')
        local db_name=$(echo "$db_url" | sed -E 's/.*\/([^:]+)$/\1/')
        local db_user=$(echo "$db_url" | sed -E 's/.*:\/\/([^:]+):.*/\1/')
        local db_pass=$(echo "$db_url" | sed -E 's/.*:\/\/[^:]+:([^@]+)@.*/\1/')
        
        # Set password temporarily in environment variable
        export PGPASSWORD="$db_pass"
        
        # Create backup directory if it doesn't exist
        mkdir -p "/Users/ivanpeychev/saas/maily/backups"
        
        # Execute pg_dump
        pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -F c -f "/Users/ivanpeychev/saas/maily/backups/$backup_file"
        
        # Unset password
        unset PGPASSWORD
        
        success "Backup created at: /Users/ivanpeychev/saas/maily/backups/$backup_file"
    fi
}

# Migrate schema only
migrate_schema() {
    log "Migrating schema from $SOURCE_ENV to $TARGET_ENV..."
    
    if [ "$DRY_RUN" = true ]; then
        log "Would migrate schema (tables, indexes, constraints, etc.)"
    else
        # Extract connection details
        local source_db_host=$(echo "$SOURCE_DB_URL" | sed -E 's/.*@([^:]+):.*/\1/')
        local source_db_port=$(echo "$SOURCE_DB_URL" | sed -E 's/.*:([0-9]+)\/.*/\1/')
        local source_db_name=$(echo "$SOURCE_DB_URL" | sed -E 's/.*\/([^:]+)$/\1/')
        local source_db_user=$(echo "$SOURCE_DB_URL" | sed -E 's/.*:\/\/([^:]+):.*/\1/')
        local source_db_pass=$(echo "$SOURCE_DB_URL" | sed -E 's/.*:\/\/[^:]+:([^@]+)@.*/\1/')
        
        local target_db_host=$(echo "$TARGET_DB_URL" | sed -E 's/.*@([^:]+):.*/\1/')
        local target_db_port=$(echo "$TARGET_DB_URL" | sed -E 's/.*:([0-9]+)\/.*/\1/')
        local target_db_name=$(echo "$TARGET_DB_URL" | sed -E 's/.*\/([^:]+)$/\1/')
        local target_db_user=$(echo "$TARGET_DB_URL" | sed -E 's/.*:\/\/([^:]+):.*/\1/')
        local target_db_pass=$(echo "$TARGET_DB_URL" | sed -E 's/.*:\/\/[^:]+:([^@]+)@.*/\1/')
        
        # Create temporary schema migration file
        local temp_file=$(mktemp)
        
        # Export schema only from source
        export PGPASSWORD="$source_db_pass"
        pg_dump -h "$source_db_host" -p "$source_db_port" -U "$source_db_user" -d "$source_db_name" --schema-only -f "$temp_file"
        unset PGPASSWORD
        
        # Apply schema to target
        export PGPASSWORD="$target_db_pass"
        psql -h "$target_db_host" -p "$target_db_port" -U "$target_db_user" -d "$target_db_name" -f "$temp_file"
        unset PGPASSWORD
        
        # Remove temporary file
        rm "$temp_file"
        
        success "Schema migration completed"
    fi
}

# Migrate data
migrate_data() {
    local include_seed=$1
    log "Migrating data from $SOURCE_ENV to $TARGET_ENV..."
    
    if [ "$DRY_RUN" = true ]; then
        if [ "$include_seed" = true ]; then
            log "Would migrate all data including seed data"
        else
            log "Would migrate user data (excluding seed data)"
        fi
    else
        # Extract connection details
        local source_db_host=$(echo "$SOURCE_DB_URL" | sed -E 's/.*@([^:]+):.*/\1/')
        local source_db_port=$(echo "$SOURCE_DB_URL" | sed -E 's/.*:([0-9]+)\/.*/\1/')
        local source_db_name=$(echo "$SOURCE_DB_URL" | sed -E 's/.*\/([^:]+)$/\1/')
        local source_db_user=$(echo "$SOURCE_DB_URL" | sed -E 's/.*:\/\/([^:]+):.*/\1/')
        local source_db_pass=$(echo "$SOURCE_DB_URL" | sed -E 's/.*:\/\/[^:]+:([^@]+)@.*/\1/')
        
        local target_db_host=$(echo "$TARGET_DB_URL" | sed -E 's/.*@([^:]+):.*/\1/')
        local target_db_port=$(echo "$TARGET_DB_URL" | sed -E 's/.*:([0-9]+)\/.*/\1/')
        local target_db_name=$(echo "$TARGET_DB_URL" | sed -E 's/.*\/([^:]+)$/\1/')
        local target_db_user=$(echo "$TARGET_DB_URL" | sed -E 's/.*:\/\/([^:]+):.*/\1/')
        local target_db_pass=$(echo "$TARGET_DB_URL" | sed -E 's/.*:\/\/[^:]+:([^@]+)@.*/\1/')
        
        # Create temporary data migration file
        local temp_file=$(mktemp)
        
        # Export data from source
        export PGPASSWORD="$source_db_pass"
        if [ "$include_seed" = true ]; then
            # Export all data
            pg_dump -h "$source_db_host" -p "$source_db_port" -U "$source_db_user" -d "$source_db_name" --data-only -f "$temp_file"
        else
            # Export only user data (excluding seed data tables)
            pg_dump -h "$source_db_host" -p "$source_db_port" -U "$source_db_user" -d "$source_db_name" --data-only \
                --exclude-table=seed_data --exclude-table=demo_data -f "$temp_file"
        fi
        unset PGPASSWORD
        
        # Apply data to target
        export PGPASSWORD="$target_db_pass"
        psql -h "$target_db_host" -p "$target_db_port" -U "$target_db_user" -d "$target_db_name" -f "$temp_file"
        unset PGPASSWORD
        
        # Remove temporary file
        rm "$temp_file"
        
        success "Data migration completed"
    fi
}

# Execute migration process
main() {
    log "Starting database migration process..."
    
    # Create backup if requested
    if [ "$WITH_BACKUP" = true ]; then
        create_backup "$TARGET_ENV" "$TARGET_DB_URL"
    fi
    
    # Migrate schema
    migrate_schema
    
    # Migrate data if not schema-only
    if [ "$SCHEMA_ONLY" = false ]; then
        migrate_data "$WITH_SEED_DATA"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        success "Dry run completed. No changes were made."
    else
        success "Migration from $SOURCE_ENV to $TARGET_ENV completed successfully."
    fi
}

# Run main function
main 