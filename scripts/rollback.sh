
#!/bin/bash
# Maily Rollback Script
# This script provides rollback functionality for the Maily deployment
# Usage: ./rollback.sh [environment] [deployment_id]

set -e

# Check if environment argument is provided
if [ -z "$1" ]; then
  echo "Error: No environment specified"
  echo "Usage: ./rollback.sh [environment] [deployment_id]"
  echo "Example: ./rollback.sh production production-20250301-123456"
  exit 1
fi

# Check if deployment_id argument is provided
if [ -z "$2" ]; then
  echo "Error: No deployment_id specified"
  echo "Usage: ./rollback.sh [environment] [deployment_id]"
  echo "Example: ./rollback.sh production production-20250301-123456"
  exit 1
fi

ENVIRONMENT="$1"
DEPLOYMENT_ID="$2"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="deployment_logs/rollback_${ENVIRONMENT}_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Rolling back deployment for ${ENVIRONMENT} to ${DEPLOYMENT_ID}..."
mkdir -p deployment_logs

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

# Function to confirm action
confirm() {
  read -p "Do you want to continue with rollback? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback aborted."
    exit 1
  fi
}

# Load environment variables
step "Loading environment variables"
if [ -f ".env.${ENVIRONMENT}" ]; then
  source ./scripts/source-env.sh "$ENVIRONMENT"
  success "Environment variables loaded"
else
  error ".env.${ENVIRONMENT} file not found"
fi

# Check what components to roll back
step "Select components to roll back"
echo "1. All components (Vercel, Kubernetes, Database)"
echo "2. Vercel deployments only"
echo "3. Kubernetes deployments only"
echo "4. Database migrations only"
read -p "Enter your choice (1-4): " component_choice

# Confirm rollback
echo -e "${YELLOW}WARNING: Rolling back will revert the system to a previous state.${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Deployment ID to roll back to: ${DEPLOYMENT_ID}"
confirm

# Rollback Vercel deployments if selected
if [[ "$component_choice" == "1" || "$component_choice" == "2" ]]; then
  step "Rolling back Vercel deployments"

  # Check if Vercel CLI is installed
  if ! command -v vercel &> /dev/null; then
    step "Installing Vercel CLI"
    run_command "npm install -g vercel" "Failed to install Vercel CLI"
    success "Vercel CLI installed"
  fi

  # Authenticate with Vercel
  step "Authenticating with Vercel"
  run_command "vercel login --token $VERCEL_TOKEN" "Failed to authenticate with Vercel"
  success "Authenticated with Vercel"

  # List deployments to find the one to roll back to
  step "Finding previous deployment"

  # Roll back frontend
  step "Rolling back frontend deployment"
  cd apps/web
  run_command "vercel rollback --scope $VERCEL_ORG_ID --token $VERCEL_TOKEN" "Frontend rollback failed"
  success "Frontend rolled back"
  cd ../..

  # Roll back API
  step "Rolling back API deployment"
  cd apps/api
  run_command "vercel rollback --scope $VERCEL_ORG_ID --token $VERCEL_TOKEN" "API rollback failed"
  success "API rolled back"
  cd ../..
fi

# Rollback Kubernetes deployments if selected
if [[ "$component_choice" == "1" || "$component_choice" == "3" ]]; then
  step "Rolling back Kubernetes deployments"

  # Find the kubectl context
  KUBE_CONTEXT=$(kubectl config current-context)
  echo "Using Kubernetes context: ${KUBE_CONTEXT}"

  # Roll back AI service deployment
  step "Rolling back AI service deployment"
  run_command "kubectl rollout undo deployment/maily-ai-service -n maily-${ENVIRONMENT}" "AI service rollback failed"

  # Wait for rollback to complete
  step "Waiting for rollback to complete"
  run_command "kubectl rollout status deployment/maily-ai-service -n maily-${ENVIRONMENT}" "AI service rollout status check failed"

  success "Kubernetes deployments rolled back"
fi

# Rollback database migrations if selected
if [[ "$component_choice" == "1" || "$component_choice" == "4" ]]; then
  step "Rolling back database migrations"

  warning "Database rollback is a complex operation. It's recommended to restore from a backup."

  echo "Options:"
  echo "1. Restore from latest backup"
  echo "2. Run down migrations"
  read -p "Enter your choice (1-2): " db_choice

  if [[ "$db_choice" == "1" ]]; then
    step "Restoring database from backup"

    # Install Supabase CLI if not already installed
    if ! command -v supabase &> /dev/null; then
      run_command "npm install -g supabase" "Supabase CLI installation failed"
    fi

    # List backups
    run_command "supabase db backups list --db-url \"$DATABASE_URL\"" "Failed to list database backups"

    # Ask for backup ID
    read -p "Enter backup ID to restore: " backup_id

    # Restore backup
    run_command "supabase db backups restore $backup_id --db-url \"$DATABASE_URL\"" "Database backup restoration failed"

  elif [[ "$db_choice" == "2" ]]; then
    step "Running down migrations"

    # This assumes you're using a migration tool that supports down migrations
    run_command "supabase migration down --db-url \"$DATABASE_URL\"" "Database migration down failed"
  fi

  success "Database rolled back"
fi

# Verify the rollback
step "Verifying rollback"
if [[ "$component_choice" == "1" || "$component_choice" == "2" ]]; then
  echo "Frontend URL: https://justmaily.com"
  echo "API URL: https://api.justmaily.com"
fi

if [[ "$component_choice" == "1" || "$component_choice" == "3" ]]; then
  run_command "kubectl get pods -n maily-${ENVIRONMENT}" "Failed to get pod status"
fi

# Create rollback report
step "Creating rollback report"
REPORT_FILE="rollback-report-${ENVIRONMENT}-${TIMESTAMP}.md"

cat > $REPORT_FILE << EOL
# Maily Rollback Report

**Environment**: ${ENVIRONMENT}
**Rollback Timestamp**: $(date)
**Rolled Back From**: Current deployment
**Rolled Back To**: ${DEPLOYMENT_ID}

## Components Rolled Back

$([ "$component_choice" == "1" ] && echo "- All components" || echo "")
$([ "$component_choice" == "2" ] || [ "$component_choice" == "1" ] && echo "- Vercel deployments (Frontend and API)" || echo "")
$([ "$component_choice" == "3" ] || [ "$component_choice" == "1" ] && echo "- Kubernetes deployments (AI Services)" || echo "")
$([ "$component_choice" == "4" ] || [ "$component_choice" == "1" ] && echo "- Database migrations" || echo "")

## Current State

\`\`\`
$(kubectl get pods -n maily-${ENVIRONMENT} 2>/dev/null || echo "No Kubernetes status available")
\`\`\`

## Next Steps

1. Verify system functionality
2. Check logs for any errors
3. Monitor system for 24 hours
4. Address the issues that caused the need for rollback
EOL

success "Rollback report created: ${REPORT_FILE}"

echo -e "\n${GREEN}=======================${NC}"
echo -e "${GREEN}Rollback Complete${NC}"
echo -e "${GREEN}=======================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Rolled back to: ${DEPLOYMENT_ID}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo "Report file: ${REPORT_FILE}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify system functionality"
echo "2. Check logs for any errors"
echo "3. Monitor system for 24 hours"
echo -e "${GREEN}=======================${NC}"

exit 0
