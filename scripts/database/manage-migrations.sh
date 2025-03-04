#!/bin/bash
# Consolidated Database Migration Manager
# Combines functionality from multiple database-related scripts
# Provides a unified interface for database migrations and management

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-maily}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
MIGRATION_DIR="${MIGRATION_DIR:-./database/migrations}"
SNAPSHOT_DIR="${SNAPSHOT_DIR:-./database/snapshots}"
BACKUP_DIR="${BACKUP_DIR:-./database/backups}"
ENV="${ENV:-development}"
OPERATION="${OPERATION:-status}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
  echo -e "${BLUE}=================================================="
  echo -e "       MAILY DATABASE MIGRATION MANAGER       "
  echo -e "==================================================${NC}"
  echo ""
  echo -e "Operation: ${OPERATION}"
  echo -e "Environment: ${ENV}"
  echo -e "Database: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"
  echo ""
}

# Logging functions
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

# Check dependencies
check_dependencies() {
  log "Checking dependencies..."

  missing_deps=()
  
  # Check for required tools
  for tool in psql pg_dump createdb pg_restore jq; do
    if ! command -v "${tool}" &> /dev/null; then
      missing_deps+=("${tool}")
    fi
  done
  
  # Check for Prisma if using it
  if [ "${USE_PRISMA}" = "true" ]; then
    for tool in npx prisma; do
      if ! command -v "${tool}" &> /dev/null; then
        missing_deps+=("${tool}")
      fi
    done
  fi
  
  if [ ${#missing_deps[@]} -gt 0 ]; then
    error "Missing dependencies: ${missing_deps[*]}"
    error "Please install missing dependencies and try again"
    exit 1
  fi
  
  log "All required dependencies are installed"
}

# Load environment variables
load_env() {
  log "Loading environment for ${ENV}..."
  
  # Set environment file
  ENV_FILE=".env"
  case ${ENV} in
    production)
      ENV_FILE=".env.production"
      ;;
    staging)
      ENV_FILE=".env.staging"
      ;;
    development)
      ENV_FILE=".env.development"
      ;;
    *)
      warn "Unknown environment: ${ENV}, using default .env file"
      ;;
  esac
  
  # Load environment if file exists
  if [ -f "${ENV_FILE}" ]; then
    log "Loading environment from ${ENV_FILE}"
    set -a
    source "${ENV_FILE}"
    set +a
  else
    warn "Environment file not found: ${ENV_FILE}"
  fi
  
  # Override with any environment variables passed explicitly
  DB_HOST="${DB_HOST:-$POSTGRES_HOST}"
  DB_PORT="${DB_PORT:-$POSTGRES_PORT}"
  DB_NAME="${DB_NAME:-$POSTGRES_DB}"
  DB_USER="${DB_USER:-$POSTGRES_USER}"
  DB_PASSWORD="${DB_PASSWORD:-$POSTGRES_PASSWORD}"
  
  # Validate required variables
  if [ -z "${DB_HOST}" ] || [ -z "${DB_NAME}" ] || [ -z "${DB_USER}" ]; then
    error "Missing required database configuration"
    error "Please set DB_HOST, DB_NAME, and DB_USER"
    exit 1
  fi
}

# Create connection string
create_connection_string() {
  if [ -z "${DB_PASSWORD}" ]; then
    CONNECTION_STRING="postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  else
    CONNECTION_STRING="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  fi
}

# Check database connection
check_connection() {
  log "Checking database connection..."
  
  if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c '\q' &> /dev/null; then
    log "Database connection successful"
  else
    error "Failed to connect to database"
    error "Please check your database credentials and connectivity"
    exit 1
  fi
}

# Create a new migration
create_migration() {
  log "Creating new migration: ${MIGRATION_NAME}..."
  
  if [ -z "${MIGRATION_NAME}" ]; then
    error "Migration name is required"
    error "Usage: $0 --operation create --name <migration_name>"
    exit 1
  fi
  
  # Create migrations directory if it doesn't exist
  mkdir -p "${MIGRATION_DIR}"
  
  # Create timestamp
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  
  # Create migration files
  MIGRATION_FILE="${MIGRATION_DIR}/${TIMESTAMP}_${MIGRATION_NAME}.sql"
  ROLLBACK_FILE="${MIGRATION_DIR}/${TIMESTAMP}_${MIGRATION_NAME}_rollback.sql"
  
  # Create migration file
  cat > "${MIGRATION_FILE}" << EOF
-- Migration: ${MIGRATION_NAME}
-- Created at: $(date)
-- Description: 

-- Write your migration SQL statements here

EOF
  
  # Create rollback file
  cat > "${ROLLBACK_FILE}" << EOF
-- Rollback for migration: ${MIGRATION_NAME}
-- Created at: $(date)
-- Description: 

-- Write your rollback SQL statements here

EOF
  
  log "Migration created: ${MIGRATION_FILE}"
  log "Rollback created: ${ROLLBACK_FILE}"
  log "Please edit these files to add your SQL statements"
}

# Apply pending migrations
apply_migrations() {
  log "Applying pending migrations..."
  
  # Create migrations directory if it doesn't exist
  mkdir -p "${MIGRATION_DIR}"
  
  # Get list of applied migrations
  if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "CREATE TABLE IF NOT EXISTS schema_migrations (version varchar PRIMARY KEY, applied_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);" &> /dev/null; then
    error "Failed to create schema_migrations table"
    exit 1
  fi
  
  # Get applied migrations
  APPLIED_MIGRATIONS=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT version FROM schema_migrations ORDER BY version;" 2>/dev/null | tr -d ' ')
  
  # Get all migration files
  MIGRATION_FILES=$(find "${MIGRATION_DIR}" -name "*.sql" -not -name "*_rollback.sql" | sort)
  
  # Apply each migration that hasn't been applied yet
  for MIGRATION in ${MIGRATION_FILES}; do
    # Extract version from filename
    FILENAME=$(basename "${MIGRATION}")
    VERSION=${FILENAME%%_*}
    
    # Check if already applied
    if echo "${APPLIED_MIGRATIONS}" | grep -q "${VERSION}"; then
      log "Migration ${FILENAME} already applied, skipping"
      continue
    fi
    
    # Get migration name
    NAME=$(echo ${FILENAME#*_} | sed 's/\.sql$//')
    
    log "Applying migration: ${NAME} (${VERSION})"
    
    # Start transaction
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "BEGIN;" &> /dev/null
    
    # Apply migration
    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${MIGRATION}" &> /dev/null; then
      # Record migration
      PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "INSERT INTO schema_migrations (version) VALUES ('${VERSION}');" &> /dev/null
      
      # Commit transaction
      PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "COMMIT;" &> /dev/null
      
      log "Successfully applied migration: ${NAME}"
    else
      # Rollback transaction
      PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "ROLLBACK;" &> /dev/null
      
      error "Failed to apply migration: ${NAME}"
      error "Rolling back transaction"
      exit 1
    fi
  done
  
  log "All migrations applied successfully"
}

# Rollback last migration
rollback_migration() {
  log "Rolling back last migration..."
  
  # Get latest applied migration
  LATEST_VERSION=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;" 2>/dev/null | tr -d ' ')
  
  if [ -z "${LATEST_VERSION}" ]; then
    warn "No migrations to roll back"
    return 0
  fi
  
  # Find rollback file
  ROLLBACK_FILE=$(find "${MIGRATION_DIR}" -name "${LATEST_VERSION}_*_rollback.sql" | head -n 1)
  
  if [ -z "${ROLLBACK_FILE}" ]; then
    error "Rollback file not found for version ${LATEST_VERSION}"
    exit 1
  fi
  
  # Extract migration name
  FILENAME=$(basename "${ROLLBACK_FILE}")
  NAME=$(echo ${FILENAME} | sed -E 's/^[0-9]+_(.*)_rollback\.sql$/\1/')
  
  log "Rolling back migration: ${NAME} (${LATEST_VERSION})"
  
  # Start transaction
  PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "BEGIN;" &> /dev/null
  
  # Apply rollback
  if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${ROLLBACK_FILE}" &> /dev/null; then
    # Remove migration record
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "DELETE FROM schema_migrations WHERE version = '${LATEST_VERSION}';" &> /dev/null
    
    # Commit transaction
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "COMMIT;" &> /dev/null
    
    log "Successfully rolled back migration: ${NAME}"
  else
    # Rollback transaction
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "ROLLBACK;" &> /dev/null
    
    error "Failed to roll back migration: ${NAME}"
    error "Rolling back transaction"
    exit 1
  fi
}

# Show migration status
show_status() {
  log "Showing migration status..."
  
  # Get applied migrations
  APPLIED_MIGRATIONS=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT version, applied_at FROM schema_migrations ORDER BY version;" 2>/dev/null)
  
  # Get all migration files
  MIGRATION_FILES=$(find "${MIGRATION_DIR}" -name "*.sql" -not -name "*_rollback.sql" | sort)
  
  echo -e "\nMigration Status:"
  echo -e "================\n"
  echo -e "| Version      | Name                        | Status    | Applied At                 |"
  echo -e "|--------------|-----------------------------|-----------|-----------------------------|"
  
  for MIGRATION in ${MIGRATION_FILES}; do
    # Extract version and name from filename
    FILENAME=$(basename "${MIGRATION}")
    VERSION=${FILENAME%%_*}
    NAME=$(echo ${FILENAME#*_} | sed 's/\.sql$//')
    
    # Check if applied
    if echo "${APPLIED_MIGRATIONS}" | grep -q "${VERSION}"; then
      APPLIED_AT=$(echo "${APPLIED_MIGRATIONS}" | grep "${VERSION}" | awk '{print $2, $3}')
      STATUS="Applied"
    else
      APPLIED_AT="N/A"
      STATUS="Pending"
    fi
    
    # Truncate name if too long
    if [ ${#NAME} -gt 25 ]; then
      NAME="${NAME:0:22}..."
    fi
    
    echo -e "| ${VERSION} | ${NAME}                          | ${STATUS}    | ${APPLIED_AT}          |" | sed 's/ \+|/|/g'
  done
  
  echo -e "\n"
}

# Create database schema snapshot
create_snapshot() {
  log "Creating database schema snapshot..."
  
  # Create snapshots directory if it doesn't exist
  mkdir -p "${SNAPSHOT_DIR}"
  
  # Create timestamp
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  
  # Create snapshot filename
  SNAPSHOT_FILE="${SNAPSHOT_DIR}/schema_${TIMESTAMP}.sql"
  
  # Dump schema only
  if PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --schema-only -f "${SNAPSHOT_FILE}" &> /dev/null; then
    log "Schema snapshot created: ${SNAPSHOT_FILE}"
  else
    error "Failed to create schema snapshot"
    exit 1
  fi
}

# Create full database backup
create_backup() {
  log "Creating full database backup..."
  
  # Create backups directory if it doesn't exist
  mkdir -p "${BACKUP_DIR}"
  
  # Create timestamp
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  
  # Create backup filename
  BACKUP_FILE="${BACKUP_DIR}/backup_${ENV}_${TIMESTAMP}.sql"
  
  # Create backup
  if PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${BACKUP_FILE}" &> /dev/null; then
    log "Database backup created: ${BACKUP_FILE}"
    
    # Compress backup
    if command -v gzip &> /dev/null; then
      gzip "${BACKUP_FILE}"
      log "Backup compressed: ${BACKUP_FILE}.gz"
    fi
  else
    error "Failed to create database backup"
    exit 1
  fi
}

# Restore database from backup
restore_backup() {
  log "Restoring database from backup: ${BACKUP_FILE}..."
  
  if [ -z "${BACKUP_FILE}" ]; then
    error "Backup file is required"
    error "Usage: $0 --operation restore --backup-file <backup_file>"
    exit 1
  fi
  
  if [ ! -f "${BACKUP_FILE}" ]; then
    error "Backup file not found: ${BACKUP_FILE}"
    exit 1
  fi
  
  # Confirm restore
  if [ "${CONFIRM_RESTORE}" != "true" ]; then
    warn "This operation will drop and recreate the database: ${DB_NAME}"
    warn "All existing data will be lost!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "${confirm}" != "yes" ]; then
      log "Restore cancelled"
      exit 0
    fi
  fi
  
  # Create temporary database
  TEMP_DB="${DB_NAME}_restore_temp"
  
  log "Creating temporary database: ${TEMP_DB}"
  PGPASSWORD="${DB_PASSWORD}" createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${TEMP_DB}" &> /dev/null
  
  # Restore to temporary database
  if [[ "${BACKUP_FILE}" == *.gz ]]; then
    log "Restoring compressed backup..."
    gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" &> /dev/null
  else
    log "Restoring backup..."
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" -f "${BACKUP_FILE}" &> /dev/null
  fi
  
  if [ $? -ne 0 ]; then
    error "Failed to restore backup to temporary database"
    log "Dropping temporary database..."
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "DROP DATABASE ${TEMP_DB};" &> /dev/null
    exit 1
  fi
  
  # Disconnect all users from the database
  log "Disconnecting users from main database..."
  PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "
  SELECT pg_terminate_backend(pg_stat_activity.pid)
  FROM pg_stat_activity
  WHERE pg_stat_activity.datname = '${DB_NAME}'
  AND pid <> pg_backend_pid();" &> /dev/null
  
  # Drop and recreate main database
  log "Dropping and recreating main database: ${DB_NAME}"
  PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "DROP DATABASE ${DB_NAME};" &> /dev/null
  PGPASSWORD="${DB_PASSWORD}" createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" &> /dev/null
  
  # Copy from temporary database
  log "Copying data from temporary database to main database..."
  PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${TEMP_DB}" | PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" &> /dev/null
  
  # Drop temporary database
  log "Dropping temporary database..."
  PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "DROP DATABASE ${TEMP_DB};" &> /dev/null
  
  log "Database restore completed successfully"
}

# Validate migrations
validate_migrations() {
  log "Validating migrations..."
  
  # Create temporary database
  TEMP_DB="${DB_NAME}_validate_temp"
  
  log "Creating temporary database: ${TEMP_DB}"
  PGPASSWORD="${DB_PASSWORD}" createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${TEMP_DB}" &> /dev/null
  
  if [ $? -ne 0 ]; then
    error "Failed to create temporary database"
    exit 1
  fi
  
  # Set connection to temporary database
  local ORIG_DB_NAME="${DB_NAME}"
  DB_NAME="${TEMP_DB}"
  
  # Apply migrations to temporary database
  apply_migrations
  
  # Reset connection to original database
  DB_NAME="${ORIG_DB_NAME}"
  
  # Drop temporary database
  log "Dropping temporary database..."
  PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -c "DROP DATABASE ${TEMP_DB};" &> /dev/null
  
  log "Migrations validation completed successfully"
}

# Consolidate multiple migration files
consolidate_migrations() {
  log "Consolidating migrations..."
  
  if [ -z "${OUTPUT_FILE}" ]; then
    OUTPUT_FILE="${MIGRATION_DIR}/consolidated_$(date +%Y%m%d%H%M%S).sql"
  fi
  
  # Get all migration files
  MIGRATION_FILES=$(find "${MIGRATION_DIR}" -name "*.sql" -not -name "*_rollback.sql" | sort)
  
  # Create consolidated file
  cat > "${OUTPUT_FILE}" << EOF
-- Consolidated Migration
-- Created at: $(date)
-- Description: This migration consolidates all migrations up to $(date)

BEGIN;

EOF
  
  # Add each migration
  for MIGRATION in ${MIGRATION_FILES}; do
    FILENAME=$(basename "${MIGRATION}")
    log "Adding migration: ${FILENAME}"
    
    # Add comment
    echo -e "\n-- From migration: ${FILENAME}" >> "${OUTPUT_FILE}"
    
    # Add content (without transaction statements)
    cat "${MIGRATION}" | grep -v "BEGIN;" | grep -v "COMMIT;" | grep -v "ROLLBACK;" >> "${OUTPUT_FILE}"
    
    echo -e "\n" >> "${OUTPUT_FILE}"
  done
  
  # Add commit
  cat >> "${OUTPUT_FILE}" << EOF
-- Add all migrations to schema_migrations table
$(for MIGRATION in ${MIGRATION_FILES}; do
  FILENAME=$(basename "${MIGRATION}")
  VERSION=${FILENAME%%_*}
  echo "INSERT INTO schema_migrations (version) VALUES ('${VERSION}') ON CONFLICT DO NOTHING;"
done)

COMMIT;
EOF
  
  log "Migrations consolidated into: ${OUTPUT_FILE}"
}

# Run Prisma migration
run_prisma_migration() {
  log "Running Prisma migration: ${MIGRATION_NAME}..."
  
  if [ -z "${MIGRATION_NAME}" ]; then
    error "Migration name is required"
    error "Usage: $0 --operation prisma-migrate --name <migration_name>"
    exit 1
  fi
  
  # Create connection string if Prisma is used
  create_connection_string
  
  # Export database URL for Prisma
  export DATABASE_URL="${CONNECTION_STRING}"
  
  # Run Prisma migration
  npx prisma migrate dev --name "${MIGRATION_NAME}"
  
  log "Prisma migration completed"
}

# Generate Prisma client
generate_prisma_client() {
  log "Generating Prisma client..."
  
  # Create connection string if Prisma is used
  create_connection_string
  
  # Export database URL for Prisma
  export DATABASE_URL="${CONNECTION_STRING}"
  
  # Generate Prisma client
  npx prisma generate
  
  log "Prisma client generated"
}

# Parse command line arguments
usage() {
  cat << EOF
Maily Database Migration Manager

Usage: $(basename "$0") [options]

Operations:
  --operation status          Show migration status
  --operation migrate         Apply pending migrations
  --operation rollback        Rollback last migration
  --operation create          Create a new migration (requires --name)
  --operation snapshot        Create database schema snapshot
  --operation backup          Create full database backup
  --operation restore         Restore database from backup (requires --backup-file)
  --operation validate        Validate migrations
  --operation consolidate     Consolidate multiple migration files
  --operation prisma-migrate  Run Prisma migration (requires --name)
  --operation prisma-generate Generate Prisma client

Options:
  --env ENV                   Environment (development, staging, production)
  --name NAME                 Migration name (for create or prisma-migrate)
  --backup-file FILE          Backup file to restore from
  --output-file FILE          Output file for consolidated migrations
  --host HOST                 Database host
  --port PORT                 Database port
  --dbname NAME               Database name
  --username USER             Database username
  --password PASS             Database password
  --confirm-restore           Confirm restore without prompting
  --use-prisma                Use Prisma for migrations
  --help                      Show this help message

Examples:
  $(basename "$0") --operation status
  $(basename "$0") --operation migrate --env production
  $(basename "$0") --operation create --name add_users_table
  $(basename "$0") --operation backup --env production
  $(basename "$0") --operation restore --backup-file ./backup_production_20230101120000.sql
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --operation)
        OPERATION="$2"
        shift 2
        ;;
      --env)
        ENV="$2"
        shift 2
        ;;
      --name)
        MIGRATION_NAME="$2"
        shift 2
        ;;
      --backup-file)
        BACKUP_FILE="$2"
        shift 2
        ;;
      --output-file)
        OUTPUT_FILE="$2"
        shift 2
        ;;
      --host)
        DB_HOST="$2"
        shift 2
        ;;
      --port)
        DB_PORT="$2"
        shift 2
        ;;
      --dbname)
        DB_NAME="$2"
        shift 2
        ;;
      --username)
        DB_USER="$2"
        shift 2
        ;;
      --password)
        DB_PASSWORD="$2"
        shift 2
        ;;
      --confirm-restore)
        CONFIRM_RESTORE="true"
        shift
        ;;
      --use-prisma)
        USE_PRISMA="true"
        shift
        ;;
      --help)
        usage
        exit 0
        ;;
      *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
    esac
  done
}

# Main function
main() {
  parse_args "$@"
  
  print_header
  check_dependencies
  load_env
  
  # Skip connection check for some operations
  if [ "${OPERATION}" != "create" ] && [ "${OPERATION}" != "help" ]; then
    check_connection
  fi
  
  # Run requested operation
  case ${OPERATION} in
    status)
      show_status
      ;;
    migrate)
      apply_migrations
      ;;
    rollback)
      rollback_migration
      ;;
    create)
      create_migration
      ;;
    snapshot)
      create_snapshot
      ;;
    backup)
      create_backup
      ;;
    restore)
      restore_backup
      ;;
    validate)
      validate_migrations
      ;;
    consolidate)
      consolidate_migrations
      ;;
    prisma-migrate)
      run_prisma_migration
      ;;
    prisma-generate)
      generate_prisma_client
      ;;
    help)
      usage
      ;;
    *)
      error "Unknown operation: ${OPERATION}"
      usage
      exit 1
      ;;
  esac
  
  log "Operation completed successfully!"
}

# Run main function with all arguments
main "$@"
