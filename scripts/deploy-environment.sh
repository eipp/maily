#!/bin/bash
# deploy-environment.sh - Deployment script for Maily environments
# Usage: ./deploy-environment.sh [environment] [component]
# environment: production, staging, testing, development
# component: web, api, all (default)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-"development"}
COMPONENT=${2:-"all"}
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(production|staging|testing|development)$ ]]; then
    echo -e "${RED}Invalid environment: $ENVIRONMENT${NC}"
    echo -e "Valid options: production, staging, testing, development"
    exit 1
fi

# Validate component
if [[ ! "$COMPONENT" =~ ^(web|api|all)$ ]]; then
    echo -e "${RED}Invalid component: $COMPONENT${NC}"
    echo -e "Valid options: web, api, all"
    exit 1
fi

# Function for logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function for success messages
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function for warning messages
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function for error messages
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command_exists vercel; then
        error "Vercel CLI not found. Install with: npm install -g vercel"
    fi
    
    if ! command_exists aws; then
        warning "AWS CLI not found. Install for AWS deployments."
    fi
    
    if ! command_exists kubectl; then
        warning "kubectl not found. Install for Kubernetes deployments."
    fi
    
    success "Prerequisites check completed."
}

# Deploy web component
deploy_web() {
    log "Deploying web component to $ENVIRONMENT..."
    cd "$PROJECT_ROOT/apps/web" || error "Web directory not found"
    
    # Copy appropriate environment file if needed
    if [ -f ".env.$ENVIRONMENT" ]; then
        log "Using existing .env.$ENVIRONMENT file"
    else
        error "Environment file .env.$ENVIRONMENT not found"
    fi
    
    # Deploy to Vercel
    log "Deploying to Vercel..."
    vercel --prod -e NODE_ENV="$ENVIRONMENT" --build-env NODE_ENV="$ENVIRONMENT" --local-config "vercel.$ENVIRONMENT.json"
    
    success "Web component deployed to $ENVIRONMENT"
}

# Deploy API component
deploy_api() {
    log "Deploying API component to $ENVIRONMENT..."
    cd "$PROJECT_ROOT/apps/api" || error "API directory not found"
    
    # Copy appropriate environment file if needed
    if [ -f ".env.$ENVIRONMENT" ]; then
        log "Using existing .env.$ENVIRONMENT file"
    else
        error "Environment file .env.$ENVIRONMENT not found"
    fi
    
    # Deploy to Vercel
    log "Deploying to Vercel..."
    vercel --prod -e NODE_ENV="$ENVIRONMENT" --build-env NODE_ENV="$ENVIRONMENT" --local-config "vercel.$ENVIRONMENT.json"
    
    success "API component deployed to $ENVIRONMENT"
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    if ! command_exists kubectl; then
        warning "Skipping Kubernetes deployment as kubectl is not installed"
        return
    }
    
    log "Deploying Kubernetes resources for $ENVIRONMENT..."
    
    # Set Kubernetes context if needed
    # kubectl config use-context your-cluster-context
    
    # Apply namespace if it doesn't exist
    kubectl apply -f "$PROJECT_ROOT/kubernetes/namespaces/$ENVIRONMENT.yaml"
    
    # Apply deployments
    kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/maily-deployment.yaml"
    
    success "Kubernetes resources deployed for $ENVIRONMENT"
}

# Main deployment function
deploy() {
    log "Starting deployment process for environment: $ENVIRONMENT, component: $COMPONENT"
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy based on component
    if [ "$COMPONENT" = "web" ] || [ "$COMPONENT" = "all" ]; then
        deploy_web
    fi
    
    if [ "$COMPONENT" = "api" ] || [ "$COMPONENT" = "all" ]; then
        deploy_api
    fi
    
    # For production and staging, also deploy Kubernetes resources
    if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "staging" ] || [ "$ENVIRONMENT" = "testing" ]; then
        deploy_kubernetes
    fi
    
    success "Deployment completed for $ENVIRONMENT!"
    log "Access your deployment at: https://$ENVIRONMENT-app.justmaily.com (or the appropriate URL)"
}

# Start deployment
deploy 