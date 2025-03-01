#!/bin/bash
# Maily Full Deployment Script
# This script orchestrates the complete deployment process for Maily in production

set -e

# Default values
ENVIRONMENT="production"
SKIP_INFRASTRUCTURE=false
SKIP_DATABASE=false
SKIP_KUBERNETES=false
SKIP_VERCEL=false
SKIP_TESTS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-infrastructure)
      SKIP_INFRASTRUCTURE=true
      shift
      ;;
    --skip-database)
      SKIP_DATABASE=true
      shift
      ;;
    --skip-kubernetes)
      SKIP_KUBERNETES=true
      shift
      ;;
    --skip-vercel)
      SKIP_VERCEL=true
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --help)
      echo "Usage: ./full-deploy.sh [options]"
      echo ""
      echo "Options:"
      echo "  --skip-infrastructure   Skip infrastructure deployment"
      echo "  --skip-database         Skip database migrations"
      echo "  --skip-kubernetes       Skip Kubernetes deployments"
      echo "  --skip-vercel           Skip Vercel deployments"
      echo "  --skip-tests            Skip tests and verification"
      echo "  --help                  Display this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Configuration
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="deployment_logs"
LOG_FILE="${LOG_DIR}/full_deployment_${ENVIRONMENT}_${TIMESTAMP}.log"
DEPLOYMENT_ID="${ENVIRONMENT}-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p $LOG_DIR

# Display banner
echo -e "${CYAN}"
echo "======================================================================"
echo "                   MAILY FULL DEPLOYMENT"
echo "======================================================================"
echo -e "${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Deployment ID: ${DEPLOYMENT_ID}"
echo "Timestamp: $(date)"
echo "Logs: ${LOG_FILE}"
echo ""

# Log deployment start
echo "=====================================================================" | tee -a $LOG_FILE
echo "Starting Maily Full Deployment (${DEPLOYMENT_ID})" | tee -a $LOG_FILE
echo "Environment: ${ENVIRONMENT}" | tee -a $LOG_FILE
echo "Timestamp: $(date)" | tee -a $LOG_FILE
echo "=====================================================================" | tee -a $LOG_FILE

# Function to display section headers
section() {
  echo -e "\n${MAGENTA}## $1 ##${NC}" | tee -a $LOG_FILE
  echo -e "${MAGENTA}$(printf '=%.0s' {1..50})${NC}" | tee -a $LOG_FILE
}

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

# Function to check if user wants to continue after a failure
confirm_continue() {
  echo -e "${YELLOW}Command failed. Do you want to continue anyway? (y/n)${NC}"
  read -r answer
  if [[ ! $answer =~ ^[Yy]$ ]]; then
    exit 1
  fi
}

# Function to make script executable
make_executable() {
  if [ -f "$1" ]; then
    chmod +x "$1"
  else
    error "File not found: $1"
  fi
}

# Make sure all scripts are executable
section "Preparing deployment scripts"
make_executable "scripts/validate-env-vars.sh"
make_executable "scripts/deploy-ai-services.sh"
make_executable "scripts/vercel-deploy.sh"
make_executable "scripts/create-k8s-secrets.sh"
make_executable "scripts/source-env.sh"

# Load environment variables
section "Loading environment variables"
step "Sourcing environment variables"
if [ -f ".env.production" ]; then
  source ./scripts/source-env.sh
  success "Environment variables loaded"
else
  error ".env.production file not found"
fi

# Validate environment variables
section "Validating environment"
step "Checking environment variables"
if ! ./scripts/validate-env-vars.sh $ENVIRONMENT; then
  error "Environment validation failed"
fi
success "Environment validation completed"

# Commit any pending changes before deployment
section "Committing changes"
step "Checking for uncommitted changes"
if git status --porcelain | grep -q .; then
  step "Committing changes before deployment"
  git add .
  git commit -m "Pre-deployment commit for ${DEPLOYMENT_ID}"
  git push origin main
  success "Changes committed and pushed"
else
  success "No changes to commit"
fi

# Infrastructure deployment
if [ "$SKIP_INFRASTRUCTURE" = false ]; then
  section "Deploying infrastructure"
  step "Applying Terraform configuration"

  cd infrastructure/terraform/eks
  run_command "terraform init" "Terraform initialization failed"
  run_command "terraform validate" "Terraform validation failed"
  run_command "terraform plan -out=production.tfplan" "Terraform plan failed"
  run_command "terraform apply production.tfplan" "Terraform apply failed"

  step "Configuring kubectl for the new cluster"
  run_command "aws eks update-kubeconfig --region $(terraform output -raw aws_region) --name $(terraform output -raw cluster_name)" "kubectl configuration failed"
  cd ../../..

  success "Infrastructure deployment completed"
else
  warning "Skipping infrastructure deployment as requested"
fi

# Database migrations
if [ "$SKIP_DATABASE" = false ]; then
  section "Running database migrations"
  step "Migrating Supabase database"

  # Install Supabase CLI if not already installed
  if ! command -v supabase &> /dev/null; then
    run_command "npm install -g supabase" "Supabase CLI installation failed"
  fi

  # Run database migrations
  run_command "supabase db push --db-url \"$DATABASE_URL\"" "Database migration failed"

  success "Database migrations completed"
else
  warning "Skipping database migrations as requested"
fi

# Kubernetes deployments
if [ "$SKIP_KUBERNETES" = false ]; then
  section "Deploying to Kubernetes"

  step "Creating Kubernetes namespace"
  run_command "kubectl apply -f kubernetes/namespaces/production.yaml" "Namespace creation failed"

  step "Creating Kubernetes secrets"
  run_command "./scripts/create-k8s-secrets.sh" "Secret creation failed"

  step "Deploying Redis"
  run_command "kubectl apply -f kubernetes/deployments/redis.yaml" "Redis deployment failed"

  step "Deploying AI services"
  run_command "./scripts/deploy-ai-services.sh $ENVIRONMENT" "AI services deployment failed"
  run_command "kubectl apply -f kubernetes/deployments/ai-service.yaml" "AI service deployment failed"

  # Wait for deployments to be ready
  step "Waiting for deployments to be ready"
  run_command "kubectl wait --for=condition=available deployment --all --namespace maily-production --timeout=300s" "Deployment readiness check failed"

  success "Kubernetes deployments completed"
else
  warning "Skipping Kubernetes deployments as requested"
fi

# Vercel deployments
if [ "$SKIP_VERCEL" = false ]; then
  section "Deploying to Vercel"

  step "Deploying frontend and API to Vercel"
  run_command "./scripts/vercel-deploy.sh $ENVIRONMENT" "Vercel deployment failed"

  success "Vercel deployments completed"
else
  warning "Skipping Vercel deployments as requested"
fi

# Run tests
if [ "$SKIP_TESTS" = false ]; then
  section "Running verification tests"

  step "Running smoke tests"
  run_command "node scripts/smoke-test.js $ENVIRONMENT" "Smoke tests failed"

  success "Verification tests passed"
else
  warning "Skipping verification tests as requested"
fi

# Create deployment report
section "Creating deployment report"
REPORT_FILE="deployment-report-${DEPLOYMENT_ID}.md"

cat > $REPORT_FILE << EOL
# Maily Deployment Report

**Deployment ID**: ${DEPLOYMENT_ID}
**Timestamp**: $(date)
**Environment**: ${ENVIRONMENT}

## Deployment Summary

$([ "$SKIP_INFRASTRUCTURE" = false ] && echo "✅ Infrastructure deployed" || echo "⏭️ Infrastructure deployment skipped")
$([ "$SKIP_DATABASE" = false ] && echo "✅ Database migrations applied" || echo "⏭️ Database migrations skipped")
$([ "$SKIP_KUBERNETES" = false ] && echo "✅ Kubernetes services deployed" || echo "⏭️ Kubernetes deployment skipped")
$([ "$SKIP_VERCEL" = false ] && echo "✅ Vercel frontend and API deployed" || echo "⏭️ Vercel deployment skipped")
$([ "$SKIP_TESTS" = false ] && echo "✅ Verification tests passed" || echo "⏭️ Verification tests skipped")

## Infrastructure Details

$([ "$SKIP_INFRASTRUCTURE" = false ] && cat infrastructure/terraform/eks/production.tfplan | grep -A 5 "Resources:" || echo "No infrastructure details available")

## Kubernetes Resources

\`\`\`
$(kubectl get all -n maily-production 2>/dev/null || echo "No Kubernetes resources found")
\`\`\`

## Vercel Deployments

$([ "$SKIP_VERCEL" = false ] && echo "Frontend URL: https://justmaily.com" || echo "No Vercel deployment details available")
$([ "$SKIP_VERCEL" = false ] && echo "API URL: https://api.justmaily.com" || echo "")

## Next Steps

1. Monitor system health in Grafana
2. Verify all features are working correctly
3. Monitor logs for any issues

## Rollback Information

If rollback is needed, use the following command:
\`\`\`
./scripts/rollback.sh production ${DEPLOYMENT_ID}
\`\`\`
EOL

success "Deployment report created: ${REPORT_FILE}"

# Display completion message
echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}                   DEPLOYMENT COMPLETED SUCCESSFULLY${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Deployment ID: ${DEPLOYMENT_ID}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo "Report file: ${REPORT_FILE}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Monitor system health for 24 hours"
echo "2. Verify all features are working correctly"
echo "3. Check logs for any issues"
echo -e "${GREEN}=====================================================================${NC}"

exit 0
