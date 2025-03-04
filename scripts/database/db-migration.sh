#!/bin/bash
# Database Migration Script for Maily
# This script handles database migrations for different environments

set -e

# Default values
ENVIRONMENT="${1:-development}"
ACTION="${2:-migrate}"
TARGET_MIGRATION="${3:-}"
LOG_DIR="deployment_logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/db_migration_${ENVIRONMENT}_${TIMESTAMP}.log"
SUPABASE_MIGRATIONS_DIR="supabase/migrations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p $LOG_DIR

# Display banner
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}                   MAILY DATABASE MIGRATION${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Action: ${ACTION}"
echo "Target Migration: ${TARGET_MIGRATION}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo ""

# Log start
echo "====================================================================" | tee -a $LOG_FILE
echo "Starting Maily Database Migration (${ENVIRONMENT})" | tee -a $LOG_FILE
echo "Action: ${ACTION}" | tee -a $LOG_FILE
echo "Target Migration: ${TARGET_MIGRATION}" | tee -a $LOG_FILE
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

# Function to display info messages
info() {
  echo -e "  $1" | tee -a $LOG_FILE
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

# Load environment variables
step "Loading environment variables"
if [ -f ".env.${ENVIRONMENT}" ]; then
  source ./scripts/source-env.sh "${ENVIRONMENT}"
  success "Environment variables loaded"
else
  if [ -f ".env.production" ]; then
    warning ".env.${ENVIRONMENT} not found, using .env.production"
    source ./scripts/source-env.sh "production"
    success "Environment variables loaded from .env.production"
  else
    error "No environment file found"
  fi
fi

# Check database connection
step "Checking database connection"
if [ -z "$DATABASE_URL" ]; then
  error "DATABASE_URL is not set"
fi

# Try to connect to the database
run_command "PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DATABASE_HOST} -U ${DATABASE_USER} -d ${DATABASE_NAME} -c '\\conninfo'" "Failed to connect to database"
success "Database connection successful"

# Install or update supabase CLI if needed
step "Checking Supabase CLI"
if ! command -v supabase &> /dev/null; then
  step "Installing Supabase CLI"
  run_command "npm install -g supabase" "Failed to install Supabase CLI"
  success "Supabase CLI installed"
else
  success "Supabase CLI already installed"
fi

# Create backup before migration
step "Creating backup before migration"
BACKUP_FILE="db_backup_${ENVIRONMENT}_${TIMESTAMP}.sql"
run_command "PGPASSWORD=${DATABASE_PASSWORD} pg_dump -h ${DATABASE_HOST} -U ${DATABASE_USER} -d ${DATABASE_NAME} -f ${BACKUP_FILE}" "Failed to create database backup"
success "Database backup created: ${BACKUP_FILE}"

# Check if migration_history table exists
step "Checking migration_history table"
if ! psql "${DATABASE_URL}" -c "SELECT * FROM migration_history LIMIT 1" &> /dev/null; then
    warning "migration_history table does not exist. Creating it now."
    psql "${DATABASE_URL}" -c "
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            migration_source TEXT DEFAULT 'consolidated',
            migration_description TEXT
        );
    "
    success "migration_history table created."
fi

# Get available migrations
if [ ! -d "${SUPABASE_MIGRATIONS_DIR}" ]; then
    error "Migrations directory ${SUPABASE_MIGRATIONS_DIR} does not exist."
fi

AVAILABLE_MIGRATIONS=$(find "${SUPABASE_MIGRATIONS_DIR}" -maxdepth 1 -type d | grep -v "^${SUPABASE_MIGRATIONS_DIR}$" | sort)
if [ -z "${AVAILABLE_MIGRATIONS}" ]; then
    warning "No migrations found in ${SUPABASE_MIGRATIONS_DIR}."
    exit 0
fi

# Perform action
case "${ACTION}" in
    migrate)
        step "Applying migrations"
        
        # Get applied migrations
        APPLIED_MIGRATIONS=$(psql "${DATABASE_URL}" -t -c "SELECT migration_name FROM migration_history ORDER BY applied_at DESC;")
        
        # Apply each migration
        for MIGRATION_DIR in ${AVAILABLE_MIGRATIONS}; do
            MIGRATION_NAME=$(basename "${MIGRATION_DIR}")
            
            # Check if migration has already been applied
            if echo "${APPLIED_MIGRATIONS}" | grep -q "${MIGRATION_NAME}"; then
                info "Migration ${MIGRATION_NAME} already applied. Skipping."
                continue
            fi
            
            step "Applying migration: ${MIGRATION_NAME}"
            
            # Read migration metadata
            if [ -f "${MIGRATION_DIR}/metadata.json" ]; then
                MIGRATION_DESCRIPTION=$(jq -r '.description // ""' "${MIGRATION_DIR}/metadata.json")
            else
                MIGRATION_DESCRIPTION=""
            fi
            
            # Apply migration
            if [ -f "${MIGRATION_DIR}/migration.sql" ]; then
                if psql "${DATABASE_URL}" -f "${MIGRATION_DIR}/migration.sql"; then
                    # Record successful migration
                    psql "${DATABASE_URL}" -c "
                        INSERT INTO migration_history (migration_name, migration_description)
                        VALUES ('${MIGRATION_NAME}', '${MIGRATION_DESCRIPTION}');
                    "
                    success "Migration ${MIGRATION_NAME} applied successfully."
                else
                    error "Failed to apply migration ${MIGRATION_NAME}."
                    exit 1
                fi
            else
                warning "Migration file not found: ${MIGRATION_DIR}/migration.sql"
            fi
        done
        
        success "Migration complete."
        ;;
        
    rollback)
        step "Rolling back migrations"
        
        # Get applied migrations
        APPLIED_MIGRATIONS=$(psql "${DATABASE_URL}" -t -c "SELECT migration_name FROM migration_history ORDER BY applied_at DESC;")
        
        if [ -z "${APPLIED_MIGRATIONS}" ]; then
            warning "No migrations to roll back."
            exit 0
        fi
        
        # If a target migration is specified, roll back to that migration
        if [ -n "${TARGET_MIGRATION}" ]; then
            step "Rolling back to migration: ${TARGET_MIGRATION}"
            
            # Check if target migration exists
            if ! echo "${APPLIED_MIGRATIONS}" | grep -q "${TARGET_MIGRATION}"; then
                error "Target migration ${TARGET_MIGRATION} not found in applied migrations."
                exit 1
            fi
            
            # Find migrations to roll back
            MIGRATIONS_TO_ROLLBACK=""
            ROLLBACK_DONE=false
            
            for MIGRATION in ${APPLIED_MIGRATIONS}; do
                if [ "${MIGRATION}" = "${TARGET_MIGRATION}" ]; then
                    ROLLBACK_DONE=true
                    break
                fi
                
                MIGRATIONS_TO_ROLLBACK="${MIGRATIONS_TO_ROLLBACK} ${MIGRATION}"
            done
            
            if [ "${ROLLBACK_DONE}" = false ]; then
                error "Failed to determine migrations to roll back."
                exit 1
            fi
        else
            # Roll back the most recent migration
            MIGRATIONS_TO_ROLLBACK=$(echo "${APPLIED_MIGRATIONS}" | head -n 1)
            step "Rolling back most recent migration: ${MIGRATIONS_TO_ROLLBACK}"
        fi
        
        # Roll back each migration
        for MIGRATION_NAME in ${MIGRATIONS_TO_ROLLBACK}; do
            MIGRATION_DIR="${SUPABASE_MIGRATIONS_DIR}/${MIGRATION_NAME}"
            
            # Check if rollback file exists
            if [ ! -f "${MIGRATION_DIR}/down.sql" ]; then
                error "Rollback file not found: ${MIGRATION_DIR}/down.sql"
                exit 1
            fi
            
            step "Rolling back migration: ${MIGRATION_NAME}"
            
            # Apply rollback
            if psql "${DATABASE_URL}" -f "${MIGRATION_DIR}/down.sql"; then
                # Remove from migration history
                psql "${DATABASE_URL}" -c "
                    DELETE FROM migration_history
                    WHERE migration_name = '${MIGRATION_NAME}';
                "
                success "Migration ${MIGRATION_NAME} rolled back successfully."
            else
                error "Failed to roll back migration ${MIGRATION_NAME}."
                exit 1
            fi
        done
        
        success "Rollback complete."
        ;;
        
    reset)
        step "Resetting database schema"
        warning "This will ERASE ALL DATA in the ${ENVIRONMENT} environment database!"

        # Confirm with user
        read -p "Are you sure you want to reset the database? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Database reset aborted"
        fi

        run_command "supabase db reset --db-url \"${DATABASE_URL}\"" "Database reset failed"
        success "Database reset completed successfully"
        ;;
        
    *)
        error "Invalid action: ${ACTION}. Valid actions are: migrate, rollback, reset"
        ;;
esac

# Output success
echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}                   DATABASE OPERATION COMPLETED${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Action: ${ACTION}"
echo "Target Migration: ${TARGET_MIGRATION}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo "Backup file: ${BACKUP_FILE}"
echo -e "${GREEN}=====================================================================${NC}"

exit 0
