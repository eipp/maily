#!/bin/bash
# Environment variables validation script
# This script validates that all required environment variables are set for deployment

set -e

ENVIRONMENT="${1:-production}"
REQUIRED_VARS=(
  # AI Model Credentials
  "OPENAI_API_KEY"
  "ANTHROPIC_API_KEY"
  "GOOGLE_AI_API_KEY"

  # Database Configuration
  "DATABASE_URL"
  "DATABASE_HOST"
  "DATABASE_USER"
  "DATABASE_PASSWORD"
  "DATABASE_NAME"
  "SUPABASE_URL"
  "SUPABASE_SERVICE_ROLE_KEY"

  # Redis Configuration
  "REDIS_HOST"
  "REDIS_PORT"
  "REDIS_PASSWORD"

  # Authentication
  "JWT_SECRET_KEY"

  # Email Provider Credentials
  "RESEND_API_KEY"
  "RESEND_FROM_EMAIL"

  # Deployment Credentials
  "VERCEL_TOKEN"
  "VERCEL_ORG_ID"

  # AWS Credentials
  "AWS_ACCESS_KEY_ID"
  "AWS_SECRET_ACCESS_KEY"
  "AWS_REGION"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "Validating environment variables for ${ENVIRONMENT}..."

# Load environment variables if not already loaded
if [ -z "$OPENAI_API_KEY" ]; then
  if [ -f ".env.${ENVIRONMENT}" ]; then
    echo "Loading environment variables from .env.${ENVIRONMENT}..."
    export $(grep -v '^#' .env.${ENVIRONMENT} | xargs)
  elif [ -f ".env.production" ]; then
    echo "Loading environment variables from .env.production..."
    export $(grep -v '^#' .env.production | xargs)
  fi
fi

MISSING_VARS=()
VALID=true

# Check for required variables
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    MISSING_VARS+=("$var")
    VALID=false
  fi
done

# Check variable formats
if [[ ! -z "$DATABASE_URL" && ! "$DATABASE_URL" =~ ^postgresql://.*$ ]]; then
  echo -e "${YELLOW}WARNING: DATABASE_URL format may be incorrect. Expected format: postgresql://user:password@host:port/database${NC}"
fi

if [[ ! -z "$SUPABASE_URL" && ! "$SUPABASE_URL" =~ ^https://.*\.supabase\.co$ ]]; then
  echo -e "${YELLOW}WARNING: SUPABASE_URL format may be incorrect. Expected format: https://your-project.supabase.co${NC}"
fi

if [[ ! -z "$JWT_SECRET_KEY" && ${#JWT_SECRET_KEY} -lt 32 ]]; then
  echo -e "${YELLOW}WARNING: JWT_SECRET_KEY may be too short. Recommend at least 32 characters.${NC}"
fi

if [[ ! -z "$OPENAI_API_KEY" && ! "$OPENAI_API_KEY" =~ ^sk-.*$ ]]; then
  echo -e "${YELLOW}WARNING: OPENAI_API_KEY format may be incorrect.${NC}"
fi

# Display results
if [ "$VALID" = true ]; then
  echo -e "${GREEN}✓ All required environment variables are set.${NC}"
  exit 0
else
  echo -e "${RED}✗ Missing required environment variables:${NC}"
  for var in "${MISSING_VARS[@]}"; do
    echo " - $var"
  done
  exit 1
fi
