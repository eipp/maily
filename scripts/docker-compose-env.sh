#!/bin/bash

# Docker Compose Environment Helper
#
# This script helps run Docker Compose with environment-specific configurations
# Usage: ./scripts/docker-compose-env.sh [dev|test|prod] [command]
# Example: ./scripts/docker-compose-env.sh dev up -d

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if environment is provided
if [ -z "$1" ]; then
  echo -e "${RED}Error: Environment not specified${NC}"
  echo -e "Usage: $0 [dev|test|prod] [command]"
  echo -e "Example: $0 dev up -d"
  exit 1
fi

# Get environment and shift arguments
ENV="$1"
shift

# Check if command is provided
if [ -z "$1" ]; then
  echo -e "${RED}Error: Docker Compose command not specified${NC}"
  echo -e "Usage: $0 [dev|test|prod] [command]"
  echo -e "Example: $0 dev up -d"
  exit 1
fi

# Set environment-specific configuration
case "$ENV" in
  dev)
    ENV_FILE="${PROJECT_ROOT}/.env.dev"
    COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml:${PROJECT_ROOT}/infrastructure/docker/docker-compose.dev.yml"
    echo -e "${GREEN}Using development environment${NC}"
    ;;
  test)
    ENV_FILE="${PROJECT_ROOT}/.env.test"
    COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml:${PROJECT_ROOT}/infrastructure/docker/docker-compose.test.yml"
    echo -e "${GREEN}Using testing environment${NC}"
    ;;
  prod)
    ENV_FILE="${PROJECT_ROOT}/.env.prod"
    COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml:${PROJECT_ROOT}/infrastructure/docker/docker-compose.prod.yml"
    echo -e "${GREEN}Using production environment${NC}"
    ;;
  *)
    echo -e "${RED}Error: Invalid environment '$ENV'${NC}"
    echo -e "Valid environments: dev, test, prod"
    exit 1
    ;;
esac

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
  echo -e "${YELLOW}Warning: Environment file $ENV_FILE not found${NC}"
  echo -e "Creating a default environment file..."

  # Create default environment file based on environment
  case "$ENV" in
    dev)
      cat > "$ENV_FILE" << EOF
# Development environment variables
DATABASE_URL=postgresql://postgres:postgres@db:5432/maily
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev_secret_key
DEBUG=true
LOG_LEVEL=debug
EOF
      ;;
    test)
      cat > "$ENV_FILE" << EOF
# Testing environment variables
DATABASE_URL=postgresql://postgres:postgres@db:5432/maily_test
REDIS_URL=redis://redis:6379/0
SECRET_KEY=test_secret_key
TESTING=true
LOG_LEVEL=info
EOF
      ;;
    prod)
      cat > "$ENV_FILE" << EOF
# Production environment variables
# IMPORTANT: Replace these values with secure values for production
DATABASE_URL=postgresql://postgres:postgres@db:5432/maily
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change_me_in_production
API_URL=https://api.example.com
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=maily
REDIS_PASSWORD=redis
EOF
      echo -e "${YELLOW}Warning: Default production environment file created.${NC}"
      echo -e "${YELLOW}Please update with secure values before deploying to production.${NC}"
      ;;
  esac

  echo -e "${GREEN}Created default environment file: $ENV_FILE${NC}"
fi

# Export environment variables
export COMPOSE_FILE
export ENV_FILE

# Run Docker Compose with the specified command
echo -e "${GREEN}Running: docker-compose --env-file $ENV_FILE $@${NC}"
docker-compose --env-file "$ENV_FILE" "$@"
