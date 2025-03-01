#!/bin/bash
# This script commits all changes and then initiates the deployment process
# Usage: ./commit-and-deploy.sh [commit message] [environment]

set -e

# Default values
COMMIT_MESSAGE="${1:-Pre-deployment commit}"
ENVIRONMENT="${2:-production}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}             MAILY COMMIT AND DEPLOY (${ENVIRONMENT})${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo "Commit message: ${COMMIT_MESSAGE}"
echo "Timestamp: $(date)"
echo ""

# Function to display step information
step() {
  echo -e "${BLUE}-> $1${NC}"
}

# Function to display success messages
success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Function to display warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}"
}

# Function to display error messages and exit
error() {
  echo -e "${RED}ERROR: $1${NC}"
  exit 1
}

# Function to run a command with logging
run_command() {
  local cmd="$1"
  local error_msg="${2:-Command failed}"

  echo "$ $cmd"
  if eval "$cmd"; then
    return 0
  else
    local exit_code=$?
    error "${error_msg} (Exit code: ${exit_code})"
    return $exit_code
  fi
}

# Make sure all script files are executable
step "Making all scripts executable"
find ./scripts -name "*.sh" -exec chmod +x {} \;
find ./scripts -name "*.js" -exec chmod +x {} \;
success "All scripts are now executable"

# Add .env.production to .gitignore if not already there
step "Ensuring sensitive files are not committed"
if ! grep -q "^.env.production$" .gitignore; then
  echo -e "\n# Environment variables\n.env.production" >> .gitignore
  success "Added .env.production to .gitignore"
else
  success ".env.production already in .gitignore"
fi

# Check if there are any staged or unstaged changes
step "Checking for changes"
if ! git diff --quiet || ! git diff --staged --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  # Check for credentials in changed files
  step "Checking for credentials in changed files"
  CREDENTIAL_PATTERN='(password|token|key|secret|pwd|pass).*=.*[A-Za-z0-9_+/]{8,}'
  CREDENTIAL_FILES=$(git diff --name-only | xargs grep -l -i -E "$CREDENTIAL_PATTERN" 2>/dev/null || true)

  if [ -n "$CREDENTIAL_FILES" ]; then
    warning "Possible credentials found in these files:"
    echo "$CREDENTIAL_FILES"
    read -p "Continue with commit? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      error "Commit aborted. Please review the files for credentials."
    fi
  fi

  # Stage all changes
  step "Staging all changes"
  run_command "git add ." "Failed to stage changes"
  success "All changes staged"

  # Commit changes
  step "Committing changes"
  FULL_COMMIT_MESSAGE="${COMMIT_MESSAGE} [${ENVIRONMENT}] [${TIMESTAMP}]"
  run_command "git commit -m \"${FULL_COMMIT_MESSAGE}\"" "Failed to commit changes"
  success "Changes committed with message: ${FULL_COMMIT_MESSAGE}"

  # Push changes
  step "Pushing changes to remote"
  run_command "git push origin" "Failed to push changes"
  success "Changes pushed to remote"
else
  success "No changes to commit"
fi

# Now proceed with deployment
step "Beginning deployment process"
if [ -f "./scripts/full-deploy.sh" ]; then
  echo "Deploying using full-deploy.sh script..."

  # Ask for deployment options
  echo "Deployment options:"
  read -p "Skip infrastructure deployment? (y/n) [n]: " skip_infra
  read -p "Skip database migrations? (y/n) [n]: " skip_db
  read -p "Skip Kubernetes deployments? (y/n) [n]: " skip_k8s
  read -p "Skip Vercel deployments? (y/n) [n]: " skip_vercel
  read -p "Skip tests? (y/n) [n]: " skip_tests

  # Build options string
  OPTIONS=""
  [[ "$skip_infra" =~ ^[Yy]$ ]] && OPTIONS="$OPTIONS --skip-infrastructure"
  [[ "$skip_db" =~ ^[Yy]$ ]] && OPTIONS="$OPTIONS --skip-database"
  [[ "$skip_k8s" =~ ^[Yy]$ ]] && OPTIONS="$OPTIONS --skip-kubernetes"
  [[ "$skip_vercel" =~ ^[Yy]$ ]] && OPTIONS="$OPTIONS --skip-vercel"
  [[ "$skip_tests" =~ ^[Yy]$ ]] && OPTIONS="$OPTIONS --skip-tests"

  # Run the full deployment script
  run_command "./scripts/full-deploy.sh $OPTIONS" "Deployment failed"
  success "Deployment completed"
else
  warning "full-deploy.sh not found. Please run deployment steps manually."
  echo "1. Run './scripts/validate-env-vars.sh ${ENVIRONMENT}' to validate environment"
  echo "2. Run './scripts/db-migration.sh ${ENVIRONMENT}' to run database migrations"
  echo "3. Run './scripts/vercel-deploy.sh ${ENVIRONMENT}' to deploy to Vercel"
  echo "4. Run './scripts/deploy-ai-services.sh ${ENVIRONMENT}' to deploy AI services"
  echo "5. Run 'node scripts/smoke-test.js ${ENVIRONMENT}' to verify deployment"
fi

echo -e "\n${GREEN}=====================================================================${NC}"
echo -e "${GREEN}                   COMMIT AND DEPLOY COMPLETE${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Commit message: ${COMMIT_MESSAGE}"
echo "Timestamp: $(date)"
echo -e "${GREEN}=====================================================================${NC}"

exit 0
