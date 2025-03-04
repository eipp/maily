#!/usr/bin/env bash
# Development Environment Setup Script
# Sets up the complete development environment for the Maily project

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with colors
info() {
  echo -e "${BLUE}INFO: $1${NC}"
}

success() {
  echo -e "${GREEN}SUCCESS: $1${NC}"
}

warn() {
  echo -e "${YELLOW}WARNING: $1${NC}"
}

error() {
  echo -e "${RED}ERROR: $1${NC}"
}

# Check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check and install dependencies
check_dependencies() {
  info "Checking dependencies..."

  # Node.js
  if ! command_exists node; then
    error "Node.js is not installed. Please install Node.js 18 or later."
    exit 1
  fi

  NODE_VERSION=$(node -v | cut -d 'v' -f 2)
  if [[ "${NODE_VERSION}" < "18.0.0" ]]; then
    error "Node.js version ${NODE_VERSION} is not supported. Please upgrade to version 18 or later."
    exit 1
  fi

  success "Node.js v${NODE_VERSION} is installed"

  # npm
  if ! command_exists npm; then
    error "npm is not installed"
    exit 1
  fi

  NPM_VERSION=$(npm -v)
  success "npm v${NPM_VERSION} is installed"

  # Docker
  if ! command_exists docker; then
    warn "Docker is not installed. Some features will not work without Docker."
  else
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f 3 | cut -d ',' -f 1)
    success "Docker v${DOCKER_VERSION} is installed"
  fi

  # Docker Compose
  if ! command_exists docker-compose; then
    warn "Docker Compose is not installed. Some features will not work without Docker Compose."
  else
    DOCKER_COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f 3 | cut -d ',' -f 1)
    success "Docker Compose v${DOCKER_COMPOSE_VERSION} is installed"
  fi
}

# Setup environment variables
setup_env_variables() {
  info "Setting up environment variables..."

  if [ ! -f .env ]; then
    info "Creating .env file from .env.example"
    cp .env.example .env
    success "Created .env file"
  else
    info ".env file already exists"
  fi

  # Generate development secrets if needed
  # This is just an example, replace with your actual secret generation logic
  if grep -q "REPLACE_WITH_RANDOM_SECRET" .env; then
    info "Generating development secrets..."
    # Replace placeholders with random strings
    sed -i.bak 's/REPLACE_WITH_RANDOM_SECRET/'$(openssl rand -hex 32)'/g' .env
    rm .env.bak
    success "Generated development secrets"
  fi
}

# Install dependencies
install_dependencies() {
  info "Installing dependencies..."

  # Install npm packages
  npm ci

  success "Installed npm dependencies"
}

# Setup git hooks
setup_git_hooks() {
  info "Setting up git hooks..."

  # Make the commit-msg hook executable
  chmod +x scripts/commit-msg-hook.js

  # Create hooks directory if it doesn't exist
  mkdir -p .git/hooks

  # Create symlink to commit-msg hook
  ln -sf ../../scripts/commit-msg-hook.js .git/hooks/commit-msg

  success "Set up git hooks"
}

# Setup databases
setup_databases() {
  info "Setting up databases..."

  if command_exists docker && command_exists docker-compose; then
    info "Starting database containers..."
    docker-compose up -d postgres redis

    info "Waiting for databases to be ready..."
    sleep 5 # Simple wait, in a real script we would poll for readiness

    success "Database containers are running"
  else
    warn "Skipping database setup because Docker and/or Docker Compose is not installed"
  fi
}

# Run database migrations
run_migrations() {
  info "Running database migrations..."

  npm run prisma:migrate

  success "Database migrations completed"
}

# Seed database with development data
seed_database() {
  info "Seeding database with development data..."

  npm run prisma:seed

  success "Database seeded with development data"
}

# Setup feature flags
setup_feature_flags() {
  info "Setting up feature flags..."

  # Ensure the feature flags directory exists
  mkdir -p config/feature-flags

  # Create default development feature flags if they don't exist
  if [ ! -f config/feature-flags/development.json ]; then
    echo '{
  "flags": {
    "newUserOnboarding": true,
    "enhancedAnalytics": true,
    "newEmailEditor": true,
    "darkMode": true,
    "apiV2": true
  }
}' > config/feature-flags/development.json
    success "Created development feature flags"
  else
    info "Development feature flags already exist"
  fi
}

# Setup code quality tools
setup_code_quality() {
  info "Setting up code quality tools..."

  # Install git hooks with Husky
  npx husky install

  # Setup ESLint
  if [ ! -f .eslintrc.json ]; then
    warn "ESLint configuration not found, creating default config"
    echo '{
  "extends": ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "root": true
}' > .eslintrc.json
  fi

  # Setup Prettier
  if [ ! -f .prettierrc ]; then
    warn "Prettier configuration not found, creating default config"
    echo '{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}' > .prettierrc
  fi

  success "Set up code quality tools"
}

# Main function
main() {
  info "Starting development environment setup for Maily..."

  check_dependencies
  setup_env_variables
  install_dependencies
  setup_git_hooks
  setup_databases
  run_migrations
  seed_database
  setup_feature_flags
  setup_code_quality

  success "Development environment setup completed successfully!"
  info "You can now start the development server with: npm run dev"
}

# Run the script
main "$@"
