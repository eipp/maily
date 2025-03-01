#!/bin/bash
# Environment Loading Script
# This script sources the appropriate environment file based on the environment argument
# It ensures environment variables are loaded correctly for deployment scripts

ENVIRONMENT="${1:-production}"
ENV_FILE=".env.${ENVIRONMENT}"

# Define color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if environment file exists
if [ -f "$ENV_FILE" ]; then
  echo -e "${GREEN}Loading environment from $ENV_FILE${NC}"

  # Export all environment variables from the file
  set -a
  source "$ENV_FILE"
  set +a

  echo -e "${GREEN}Environment variables loaded successfully${NC}"
else
  # Fall back to production if specific environment file doesn't exist
  if [ "$ENVIRONMENT" != "production" ] && [ -f ".env.production" ]; then
    echo -e "${YELLOW}Warning: $ENV_FILE not found. Falling back to .env.production${NC}"

    set -a
    source ".env.production"
    set +a

    echo -e "${YELLOW}Environment variables loaded from .env.production${NC}"
  else
    echo -e "${RED}Error: Environment file $ENV_FILE not found${NC}"
    exit 1
  fi
fi

# Optional verification of critical variables
if [ -z "$ENVIRONMENT" ]; then
  echo -e "${RED}Error: ENVIRONMENT not set${NC}"
  exit 1
fi

# Display success message with some environment info (without showing sensitive data)
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "Database Host: ${GREEN}${DATABASE_HOST}${NC}"
echo -e "API URL: ${GREEN}${API_URL}${NC}"
echo -e "Frontend URL: ${GREEN}${FRONTEND_URL}${NC}"

# Return success
exit 0
