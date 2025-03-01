#!/bin/bash
# Master Deployment Script for Maily
# This is the main entry point for deploying Maily to any environment
# Usage: ./master-deploy.sh [environment]

set -e

# Default values
ENVIRONMENT="${1:-production}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DEPLOYMENT_ID="${ENVIRONMENT}-${TIMESTAMP}"
LOG_DIR="deployment_logs"
LOG_FILE="${LOG_DIR}/master_deployment_${ENVIRONMENT}_${TIMESTAMP}.log"

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
echo "                   MAILY MASTER DEPLOYMENT"
echo "======================================================================"
echo -e "${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Deployment ID: ${DEPLOYMENT_ID}"
echo "Timestamp: $(date)"
echo "Logs: ${LOG_FILE}"
echo ""

# Log deployment start
echo "=====================================================================" | tee -a $LOG_FILE
echo "Starting Maily Master Deployment (${DEPLOYMENT_ID})" | tee -a $LOG_FILE
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

# Function to ask for confirmation
confirm() {
  read -p "$1 (y/n) " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]]
}

# Ensure all scripts are executable
section "Ensuring scripts are executable"
find ./scripts -name "*.sh" -exec chmod +x {} \;
find ./scripts -name "*.js" -exec chmod +x {} \;
success "All scripts are now executable"

# Load and validate environment variables
section "Loading environment variables"
if [ -f "./scripts/source-env.sh" ]; then
  source ./scripts/source-env.sh "$ENVIRONMENT"
  success "Environment variables loaded"
else
  error "source-env.sh script not found. Cannot load environment variables."
fi

section "Validating environment variables"
if [ -f "./scripts/validate-env-vars.sh" ]; then
  ./scripts/validate-env-vars.sh "$ENVIRONMENT"
  success "Environment validation completed"
else
  error "validate-env-vars.sh script not found. Cannot validate environment variables."
fi

# Create deployment log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Confirm deployment
section "Deployment Configuration"
echo "You are about to deploy Maily to the '${ENVIRONMENT}' environment."
echo "This will deploy the following components:"
echo "1. Database migrations"
echo "2. Infrastructure (Terraform/AWS EKS)"
echo "3. Kubernetes resources (AI services, Redis, etc.)"
echo "4. Vercel deployments (Frontend and API)"
echo ""
echo "Deployment ID: ${DEPLOYMENT_ID}"
echo "Timestamp: $(date)"
echo ""

if ! confirm "Do you want to proceed with this deployment?"; then
  error "Deployment aborted by user"
fi

# Let user choose which components to deploy
section "Deployment Options"
echo "Select which components to deploy:"

if confirm "Deploy database migrations?"; then
  DEPLOY_DB=true
else
  DEPLOY_DB=false
fi

if confirm "Deploy infrastructure (Terraform/AWS EKS)?"; then
  DEPLOY_INFRA=true
else
  DEPLOY_INFRA=false
fi

if confirm "Deploy Kubernetes resources?"; then
  DEPLOY_K8S=true
else
  DEPLOY_K8S=false
fi

if confirm "Deploy to Vercel (Frontend and API)?"; then
  DEPLOY_VERCEL=true
else
  DEPLOY_VERCEL=false
fi

if confirm "Run verification tests after deployment?"; then
  RUN_TESTS=true
else
  RUN_TESTS=false
fi

# Database deployment
if [ "$DEPLOY_DB" = true ]; then
  section "Database Deployment"

  if [ -f "./scripts/db-migration.sh" ]; then
    step "Running database migrations"
    ./scripts/db-migration.sh "$ENVIRONMENT"
    success "Database migrations completed"
  else
    error "db-migration.sh script not found. Cannot run database migrations."
  fi
else
  warning "Skipping database migrations"
fi

# Infrastructure deployment
if [ "$DEPLOY_INFRA" = true ]; then
  section "Infrastructure Deployment"

  step "Deploying infrastructure with Terraform"
  cd infrastructure/terraform/eks

  run_command "terraform init" "Terraform initialization failed"
  run_command "terraform validate" "Terraform validation failed"
  run_command "terraform plan -out=tfplan" "Terraform plan failed"

  if confirm "Do you want to apply the Terraform plan?"; then
    run_command "terraform apply tfplan" "Terraform apply failed"
    success "Infrastructure deployment completed"
  else
    warning "Terraform apply skipped"
  fi

  cd ../../..

  # Configure kubectl with the new cluster
  step "Configuring kubectl"
  CLUSTER_NAME=$(terraform output -raw cluster_name 2>/dev/null || echo "maily-$ENVIRONMENT-cluster")
  run_command "aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME" "Failed to configure kubectl"
  success "kubectl configured for cluster: $CLUSTER_NAME"
else
  warning "Skipping infrastructure deployment"
fi

# Kubernetes deployment
if [ "$DEPLOY_K8S" = true ]; then
  section "Kubernetes Deployment"

  step "Creating Kubernetes namespace"
  run_command "kubectl apply -f kubernetes/namespaces/production.yaml" "Namespace creation failed"

  step "Creating Kubernetes secrets"
  if [ -f "./scripts/create-k8s-secrets.sh" ]; then
    ./scripts/create-k8s-secrets.sh
    success "Kubernetes secrets created"
  else
    error "create-k8s-secrets.sh script not found. Cannot create Kubernetes secrets."
  fi

  step "Deploying Kubernetes resources"
  run_command "kubectl apply -f kubernetes/deployments/redis.yaml" "Redis deployment failed"

  step "Deploying AI services"
  if [ -f "./scripts/deploy-ai-services.sh" ]; then
    ./scripts/deploy-ai-services.sh "$ENVIRONMENT"
    success "AI services deployment completed"
  else
    error "deploy-ai-services.sh script not found. Cannot deploy AI services."
  fi

  step "Applying AI service Kubernetes manifests"
  run_command "kubectl apply -f kubernetes/deployments/ai-service.yaml" "AI service Kubernetes deployment failed"

  step "Waiting for deployments to be ready"
  run_command "kubectl wait --for=condition=available deployment --all --namespace maily-$ENVIRONMENT --timeout=300s" "Deployment readiness check failed"
  success "All Kubernetes deployments are ready"
else
  warning "Skipping Kubernetes deployment"
fi

# Vercel deployment
if [ "$DEPLOY_VERCEL" = true ]; then
  section "Vercel Deployment"

  if [ -f "./scripts/vercel-deploy.sh" ]; then
    step "Deploying to Vercel"
    ./scripts/vercel-deploy.sh "$ENVIRONMENT"
    success "Vercel deployment completed"
  else
    error "vercel-deploy.sh script not found. Cannot deploy to Vercel."
  fi
else
  warning "Skipping Vercel deployment"
fi

# Run verification tests
if [ "$RUN_TESTS" = true ]; then
  section "Verification Tests"

  if [ -f "./scripts/smoke-test.js" ]; then
    step "Running smoke tests"
    node ./scripts/smoke-test.js "$ENVIRONMENT"
    success "Smoke tests completed"
  else
    error "smoke-test.js script not found. Cannot run verification tests."
  fi
else
  warning "Skipping verification tests"
fi

# Create deployment report
section "Creating Deployment Report"
REPORT_FILE="deployment-report-${DEPLOYMENT_ID}.md"

cat > $REPORT_FILE << EOL
# Maily Deployment Report

**Deployment ID**: ${DEPLOYMENT_ID}
**Timestamp**: $(date)
**Environment**: ${ENVIRONMENT}

## Deployment Summary

$([ "$DEPLOY_DB" = true ] && echo "✅ Database migrations applied" || echo "⏭️ Database migrations skipped")
$([ "$DEPLOY_INFRA" = true ] && echo "✅ Infrastructure deployed" || echo "⏭️ Infrastructure deployment skipped")
$([ "$DEPLOY_K8S" = true ] && echo "✅ Kubernetes services deployed" || echo "⏭️ Kubernetes deployment skipped")
$([ "$DEPLOY_VERCEL" = true ] && echo "✅ Vercel frontend and API deployed" || echo "⏭️ Vercel deployment skipped")
$([ "$RUN_TESTS" = true ] && echo "✅ Verification tests completed" || echo "⏭️ Verification tests skipped")

## Kubernetes Resources

\`\`\`
$(kubectl get all -n maily-$ENVIRONMENT 2>/dev/null || echo "No Kubernetes resources found")
\`\`\`

## Vercel Deployments

$([ "$DEPLOY_VERCEL" = true ] && echo "Frontend URL: https://justmaily.com" || echo "No Vercel deployment information available")
$([ "$DEPLOY_VERCEL" = true ] && echo "API URL: https://api.justmaily.com" || echo "")

## Next Steps

1. Monitor system health in Grafana
2. Verify all features are working correctly
3. Monitor logs for any issues

## Rollback Information

If rollback is needed, use the following command:
\`\`\`
./scripts/rollback.sh ${ENVIRONMENT} ${DEPLOYMENT_ID}
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
