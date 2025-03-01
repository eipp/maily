#!/bin/bash
# Database Migration Script for Maily
# This script handles database migrations for different environments

set -e

# Default values
ENVIRONMENT="${1:-production}"
ACTION="${2:-migrate}"
LOG_DIR="deployment_logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/db_migration_${ENVIRONMENT}_${TIMESTAMP}.log"

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
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo ""

# Log start
echo "====================================================================" | tee -a $LOG_FILE
echo "Starting Maily Database Migration (${ENVIRONMENT})" | tee -a $LOG_FILE
echo "Action: ${ACTION}" | tee -a $LOG_FILE
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

# Check if we need a schema update
if [ "${ACTION}" == "migrate" ]; then
  step "Running database migrations"
  run_command "supabase db push --db-url \"${DATABASE_URL}\"" "Database migration failed"
  success "Database migrations applied successfully"
elif [ "${ACTION}" == "rollback" ]; then
  step "Rolling back database migration"

  # Check if a specific version was provided
  if [ -n "$3" ]; then
    MIGRATION_VERSION="$3"
    run_command "supabase migration up ${MIGRATION_VERSION} --db-url \"${DATABASE_URL}\"" "Database rollback failed"
  else
    # If no version specified, rollback one migration
    run_command "supabase migration down --db-url \"${DATABASE_URL}\"" "Database rollback failed"
  fi

  success "Database rollback completed successfully"
elif [ "${ACTION}" == "reset" ]; then
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
else
  error "Unknown action: ${ACTION}. Valid actions are: migrate, rollback, reset"
fi

# Output success
echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}                   DATABASE OPERATION COMPLETED${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Action: ${ACTION}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo "Backup file: ${BACKUP_FILE}"
echo -e "${GREEN}=====================================================================${NC}"

exit 0
