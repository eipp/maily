#!/bin/bash
# Maily Vercel Deployment Script
# This script deploys the frontend and API to Vercel
# Usage: ./vercel-deploy.sh [environment]

set -e

# Check if environment argument is provided
if [ -z "$1" ]; then
  echo "Error: No environment specified"
  echo "Usage: ./vercel-deploy.sh [environment]"
  echo "Example: ./vercel-deploy.sh production"
  exit 1
fi

ENVIRONMENT="$1"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="deployment_logs/vercel_deployment_${ENVIRONMENT}_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "Deploying to Vercel (${ENVIRONMENT})"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
  step "Installing Vercel CLI"
  run_command "npm install -g vercel" "Failed to install Vercel CLI"
  success "Vercel CLI installed"
else
  success "Vercel CLI already installed"
fi

# Check required organization ID
if [ -z "$VERCEL_ORG_ID" ]; then
  warning "VERCEL_ORG_ID is not set. This may be needed for some operations."
else
  success "Required Vercel organization ID found"
fi

# Verify authentication
step "Checking Vercel authentication"
# Check if already logged in
if vercel whoami >/dev/null 2>&1; then
  success "Already authenticated with Vercel"
else
  run_command "vercel login" "Failed to authenticate with Vercel"
  success "Authenticated with Vercel"
fi

# Deploy Frontend (Next.js)
step "Deploying frontend to Vercel"
cd apps/web
if [ -d "pages" ] || [ -d "app" ] || [ -f "next.config.js" ] || [ -f "vercel.json" ]; then
  if [ "$ENVIRONMENT" = "production" ]; then
    # Production deployment
    run_command "vercel --prod" "Frontend deployment failed"
  else
    # Preview deployment
    run_command "vercel" "Frontend deployment failed"
  fi
  success "Frontend deployed to Vercel"
  cd ../..
else
  cd ../..
  error "Next.js project files not found in apps/web directory"
fi

# Deploy API
step "Deploying API to Vercel"
cd apps/api
if [ -f "vercel.json" ] || [ -d "api" ]; then
  if [ "$ENVIRONMENT" = "production" ]; then
    # Production deployment
    run_command "vercel --prod" "API deployment failed"
  else
    # Preview deployment
    run_command "vercel" "API deployment failed"
  fi
  success "API deployed to Vercel"
  cd ../..
else
  cd ../..
  warning "API deployment files not found in apps/api directory. Skipping API deployment."
fi

# Configure Project Aliases
step "Configuring domain aliases"
if [ "$ENVIRONMENT" = "production" ]; then
  # Production domains
  run_command "vercel alias set apps/web/$(vercel ls | grep apps/web | head -n 1 | awk '{print $2}') justmaily.com" "Failed to set frontend domain alias"
  run_command "vercel alias set apps/api/$(vercel ls | grep apps/api | head -n 1 | awk '{print $2}') api.justmaily.com" "Failed to set API domain alias"
fi
success "Domain aliases configured"

# Set environment variables for Vercel project
step "Setting environment variables on Vercel"
run_command "vercel env add NEXT_PUBLIC_API_URL https://api.justmaily.com" "Failed to set API URL environment variable"
if [ ! -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
  run_command "vercel env add NEXT_PUBLIC_SUPABASE_URL $NEXT_PUBLIC_SUPABASE_URL" "Failed to set Supabase URL environment variable"
fi
if [ ! -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
  run_command "vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY $NEXT_PUBLIC_SUPABASE_ANON_KEY" "Failed to set Supabase anon key environment variable"
fi
if [ ! -z "$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" ]; then
  run_command "vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY $NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" "Failed to set Clerk key environment variable"
fi
success "Environment variables set on Vercel"

# Verify deployment
step "Verifying deployment"
if [ "$ENVIRONMENT" = "production" ]; then
  echo "Frontend URL: https://justmaily.com"
  echo "API URL: https://api.justmaily.com"
else
  echo "Check Vercel dashboard for preview URLs"
fi

echo -e "\n${GREEN}=======================${NC}"
echo -e "${GREEN}Vercel Deployment Complete${NC}"
echo -e "${GREEN}=======================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify frontend and API are working correctly"
echo "2. Check DNS propagation for custom domains"
echo "3. Run monitoring tests to verify performance"
echo -e "${GREEN}=======================${NC}"

exit 0
