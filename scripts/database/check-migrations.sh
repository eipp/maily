#!/bin/bash
# Migration Check Script for Maily
# This script checks if any migrations need to be applied

set -e

# Default values
ENVIRONMENT="${1:-development}"
LOG_DIR="deployment_logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/migration_check_${ENVIRONMENT}_${TIMESTAMP}.log"

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
echo -e "${BLUE}                   MAILY MIGRATION CHECK${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo ""

# Functions
step() {
  echo -e "${BLUE}-> $1${NC}" | tee -a $LOG_FILE
}

success() {
  echo -e "${GREEN}✓ $1${NC}" | tee -a $LOG_FILE
}

warning() {
  echo -e "${YELLOW}! $1${NC}" | tee -a $LOG_FILE
}

error() {
  echo -e "${RED}ERROR: $1${NC}" | tee -a $LOG_FILE
  exit 1
}

# Load environment variables
step "Loading environment variables"
if [ -f ".env.${ENVIRONMENT}" ]; then
  source ./scripts/source-env.sh "${ENVIRONMENT}"
  success "Environment variables loaded"
else
  if [ -f ".env" ]; then
    warning ".env.${ENVIRONMENT} not found, using .env"
    source ./scripts/source-env.sh
    success "Environment variables loaded from .env"
  else
    error "No environment file found"
  fi
fi

# Check database connection
step "Checking database connection"
if [ -z "$DATABASE_URL" ]; then
  warning "DATABASE_URL is not set, attempting to use individual connection parameters"
  if [ -z "$DATABASE_HOST" ] || [ -z "$DATABASE_USER" ] || [ -z "$DATABASE_NAME" ]; then
    error "Database connection parameters are not set"
  fi
else
  # Parse the DATABASE_URL to get connection details
  DB_REGEX="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
  if [[ $DATABASE_URL =~ $DB_REGEX ]]; then
    DATABASE_USER="${BASH_REMATCH[1]}"
    DATABASE_PASSWORD="${BASH_REMATCH[2]}"
    DATABASE_HOST="${BASH_REMATCH[3]}"
    DATABASE_PORT="${BASH_REMATCH[4]}"
    DATABASE_NAME="${BASH_REMATCH[5]}"
  else
    error "Failed to parse DATABASE_URL"
  fi
fi

# Check for migration history table
step "Checking for migration history table"
MIGRATION_TABLE_EXISTS=$(PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DATABASE_HOST} -U ${DATABASE_USER} -d ${DATABASE_NAME} -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'migration_history')" 2>> $LOG_FILE)

if [[ $MIGRATION_TABLE_EXISTS == *"t"* ]]; then
  success "Migration history table exists"
else
  warning "Migration history table does not exist. Database may need initialization."
  exit 0
fi

# Get all available migrations
step "Getting available migrations"
AVAILABLE_MIGRATIONS=$(find "supabase/migrations" -type d -name "*_*" | sort)
MIGRATION_COUNT=$(echo "$AVAILABLE_MIGRATIONS" | wc -l)
MIGRATION_COUNT=$((MIGRATION_COUNT))

if [ $MIGRATION_COUNT -eq 0 ]; then
  warning "No migrations found"
  exit 0
fi

success "Found ${MIGRATION_COUNT} available migrations"

# Get applied migrations
step "Getting applied migrations"
APPLIED_MIGRATIONS=$(PGPASSWORD=${DATABASE_PASSWORD} psql -h ${DATABASE_HOST} -U ${DATABASE_USER} -d ${DATABASE_NAME} -t -c "SELECT migration_name FROM migration_history ORDER BY applied_at" 2>> $LOG_FILE)
APPLIED_COUNT=$(echo "$APPLIED_MIGRATIONS" | grep -v "^$" | wc -l)
APPLIED_COUNT=$((APPLIED_COUNT))

success "Found ${APPLIED_COUNT} applied migrations"

# Compare and check for pending migrations
step "Checking for pending migrations"

if [ $APPLIED_COUNT -eq $MIGRATION_COUNT ]; then
  success "Database schema is up to date. No migrations needed."
  exit 0
else
  PENDING_COUNT=$((MIGRATION_COUNT - APPLIED_COUNT))
  warning "${PENDING_COUNT} migrations need to be applied"
  
  echo -e "\n${YELLOW}Pending migrations:${NC}"
  for MIGRATION_DIR in $AVAILABLE_MIGRATIONS; do
    MIGRATION_NAME=$(basename "$MIGRATION_DIR")
    if ! echo "$APPLIED_MIGRATIONS" | grep -q "$MIGRATION_NAME"; then
      echo "- $MIGRATION_NAME"
    fi
  done
  
  echo -e "\n${BLUE}To apply migrations, run:${NC}"
  echo "./scripts/db-migration.sh ${ENVIRONMENT} migrate"
  exit 1
fi 