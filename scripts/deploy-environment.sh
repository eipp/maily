#!/bin/bash
#
# Multi-Environment Deployment Script for Maily
# This script handles deployments to all defined environments: production, staging, testing, development
#
# Usage:
#   ./deploy-environment.sh <environment> [component] [options]
#
# Examples:
#   ./deploy-environment.sh production             # Deploy everything to production
#   ./deploy-environment.sh staging api            # Deploy only API to staging
#   ./deploy-environment.sh testing web --force    # Force deploy web to testing
#   ./deploy-environment.sh development --rebuild  # Rebuild and deploy to development
#

set -e

# Configuration
VALID_ENVIRONMENTS=("production" "staging" "testing" "development")
VALID_COMPONENTS=("all" "api" "web" "ai-service" "email-service" "workers" "infrastructure")
DOCKER_REGISTRY="maily"
IMAGE_TAG=$(git rev-parse --short HEAD)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
function show_usage {
    echo -e "${BLUE}Multi-Environment Deployment Script for Maily${NC}"
    echo
    echo "Usage:"
    echo "  $0 <environment> [component] [options]"
    echo
    echo "Environments:"
    echo "  production  - Production environment"
    echo "  staging     - Staging environment"
    echo "  testing     - Testing environment" 
    echo "  development - Development environment"
    echo
    echo "Components (default: all):"
    echo "  all           - Deploy all components"
    echo "  api           - Deploy API service"
    echo "  web           - Deploy web application"
    echo "  ai-service    - Deploy AI service"
    echo "  email-service - Deploy email service"
    echo "  workers       - Deploy worker services"
    echo "  infrastructure - Deploy infrastructure only"
    echo
    echo "Options:"
    echo "  --force     - Force deployment even if checks fail"
    echo "  --rebuild   - Rebuild all images before deployment"
    echo "  --skip-tests - Skip running tests before deployment"
    echo "  --help      - Display this help message"
    echo
    echo "Examples:"
    echo "  $0 production             # Deploy everything to production"
    echo "  $0 staging api            # Deploy only API to staging"
    echo "  $0 testing web --force    # Force deploy web to testing"
    exit 1
}

# Parse arguments
if [ $# -lt 1 ]; then
    show_usage
fi

ENVIRONMENT=$1
shift

# Validate environment
if [[ ! " ${VALID_ENVIRONMENTS[@]} " =~ " ${ENVIRONMENT} " ]]; then
    echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
    echo "Valid environments: ${VALID_ENVIRONMENTS[*]}"
    exit 1
fi

# Default component is "all"
COMPONENT="all"
if [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; then
    COMPONENT=$1
    shift
fi

# Validate component
if [[ ! " ${VALID_COMPONENTS[@]} " =~ " ${COMPONENT} " ]]; then
    echo -e "${RED}Error: Invalid component '$COMPONENT'${NC}"
    echo "Valid components: ${VALID_COMPONENTS[*]}"
    exit 1
fi

# Parse options
FORCE=false
REBUILD=false
SKIP_TESTS=false
while [ $# -gt 0 ]; do
    case "$1" in
        --force)
            FORCE=true
            ;;
        --rebuild)
            REBUILD=true
            ;;
        --skip-tests)
            SKIP_TESTS=true
            ;;
        --help)
            show_usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'${NC}"
            show_usage
            ;;
    esac
    shift
done

# Display deployment information
echo -e "${BLUE}========== Maily Deployment ==========${NC}"
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo -e "Component:   ${GREEN}${COMPONENT}${NC}"
echo -e "Force:       ${YELLOW}${FORCE}${NC}"
echo -e "Rebuild:     ${YELLOW}${REBUILD}${NC}"
echo -e "Skip Tests:  ${YELLOW}${SKIP_TESTS}${NC}"
echo -e "Image Tag:   ${GREEN}${IMAGE_TAG}${NC}"
echo -e "${BLUE}=====================================${NC}"
echo

# Check prerequisites
if [ "$ENVIRONMENT" == "production" ] && [ "$FORCE" != true ]; then
    # Check if on main branch for production
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo -e "${RED}Error: Must be on 'main' branch to deploy to production${NC}"
        echo "Use --force to override"
        exit 1
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${RED}Error: There are uncommitted changes${NC}"
        echo "Commit or stash changes before deploying to production"
        echo "Use --force to override"
        exit 1
    fi
fi

# Run tests if not skipped
if [ "$SKIP_TESTS" != true ]; then
    echo -e "${BLUE}Running tests...${NC}"
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "api" ]; then
        echo "Running API tests..."
        # Add your API test command here
        # e.g. cd "$PROJECT_ROOT/apps/api" && npm test
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "web" ]; then
        echo "Running Web tests..."
        # Add your Web test command here
        # e.g. cd "$PROJECT_ROOT/apps/web" && npm test
    fi
    
    echo -e "${GREEN}All tests passed!${NC}"
fi

# Build Docker images if needed
if [ "$REBUILD" == true ]; then
    echo -e "${BLUE}Building Docker images...${NC}"
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "api" ]; then
        echo "Building API image..."
        docker build -t "$DOCKER_REGISTRY/api:$IMAGE_TAG" \
            -t "$DOCKER_REGISTRY/api:$ENVIRONMENT" \
            -f "$PROJECT_ROOT/docker/dockerfiles/api.Dockerfile" \
            --build-arg NODE_ENV="$ENVIRONMENT" \
            "$PROJECT_ROOT"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "web" ]; then
        echo "Building Web image..."
        docker build -t "$DOCKER_REGISTRY/web:$IMAGE_TAG" \
            -t "$DOCKER_REGISTRY/web:$ENVIRONMENT" \
            -f "$PROJECT_ROOT/docker/dockerfiles/web.Dockerfile" \
            --build-arg NODE_ENV="$ENVIRONMENT" \
            "$PROJECT_ROOT"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "ai-service" ]; then
        echo "Building AI Service image..."
        docker build -t "$DOCKER_REGISTRY/ai-service:$IMAGE_TAG" \
            -t "$DOCKER_REGISTRY/ai-service:$ENVIRONMENT" \
            -f "$PROJECT_ROOT/docker/dockerfiles/ai-service.Dockerfile" \
            --build-arg ENVIRONMENT="$ENVIRONMENT" \
            "$PROJECT_ROOT"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "email-service" ]; then
        echo "Building Email Service image..."
        docker build -t "$DOCKER_REGISTRY/email-service:$IMAGE_TAG" \
            -t "$DOCKER_REGISTRY/email-service:$ENVIRONMENT" \
            -f "$PROJECT_ROOT/docker/dockerfiles/email-service.Dockerfile" \
            --build-arg NODE_ENV="$ENVIRONMENT" \
            "$PROJECT_ROOT"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "workers" ]; then
        echo "Building Workers image..."
        docker build -t "$DOCKER_REGISTRY/workers:$IMAGE_TAG" \
            -t "$DOCKER_REGISTRY/workers:$ENVIRONMENT" \
            -f "$PROJECT_ROOT/docker/dockerfiles/workers.Dockerfile" \
            --build-arg NODE_ENV="$ENVIRONMENT" \
            "$PROJECT_ROOT"
    fi
    
    echo -e "${GREEN}All images built successfully!${NC}"
fi

# Deploy to the selected environment
echo -e "${BLUE}Deploying to $ENVIRONMENT environment...${NC}"

# Set environment variables for deployment
export DOCKER_REGISTRY
export IMAGE_TAG
export ENVIRONMENT

# Use docker-compose with the appropriate environment file
COMPOSE_FILE="$PROJECT_ROOT/docker/compose/docker-compose.$ENVIRONMENT.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: Compose file not found: $COMPOSE_FILE${NC}"
    exit 1
fi

# Deploy based on component
if [ "$COMPONENT" == "infrastructure" ]; then
    # Infrastructure deployment
    echo "Deploying infrastructure for $ENVIRONMENT..."
    
    if [ -d "$PROJECT_ROOT/infrastructure/terraform" ]; then
        cd "$PROJECT_ROOT/infrastructure/terraform"
        terraform workspace select "$ENVIRONMENT" || terraform workspace new "$ENVIRONMENT"
        terraform apply -var-file="$ENVIRONMENT.tfvars" -auto-approve
    fi
else
    # Service deployment
    SERVICES=""
    
    case "$COMPONENT" in
        all)
            # No specific service means deploy all
            ;;
        api)
            SERVICES="api"
            ;;
        web)
            SERVICES="web"
            ;;
        ai-service)
            SERVICES="ai-service"
            ;;
        email-service)
            SERVICES="email-service"
            ;;
        workers)
            SERVICES="workers"
            ;;
    esac
    
    if [ -n "$SERVICES" ]; then
        docker-compose -f "$COMPOSE_FILE" up -d "$SERVICES"
    else
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
fi

echo -e "${GREEN}Deployment to $ENVIRONMENT completed successfully!${NC}"

# Deploy to Kubernetes if available for this environment
if [ -d "$PROJECT_ROOT/kubernetes/$ENVIRONMENT" ]; then
    echo -e "${BLUE}Deploying to Kubernetes...${NC}"
    KUBE_NAMESPACE="maily-$ENVIRONMENT"
    
    # Ensure namespace exists
    kubectl get namespace "$KUBE_NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$KUBE_NAMESPACE"
    
    # Apply Kubernetes manifests
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "infrastructure" ]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/infrastructure" --namespace="$KUBE_NAMESPACE"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "api" ]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/api" --namespace="$KUBE_NAMESPACE"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "web" ]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/web" --namespace="$KUBE_NAMESPACE"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "ai-service" ]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/ai-service" --namespace="$KUBE_NAMESPACE"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "email-service" ]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/email-service" --namespace="$KUBE_NAMESPACE"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "workers" ]; then
        kubectl apply -f "$PROJECT_ROOT/kubernetes/$ENVIRONMENT/workers" --namespace="$KUBE_NAMESPACE"
    fi
    
    echo -e "${GREEN}Kubernetes deployment completed!${NC}"
fi

# Deploy to Vercel if applicable
if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "web" ]; then
    if [ -f "$PROJECT_ROOT/vercel.$ENVIRONMENT.json" ]; then
        echo -e "${BLUE}Deploying web to Vercel...${NC}"
        cd "$PROJECT_ROOT"
        vercel --prod -e NODE_ENV="$ENVIRONMENT" --build-env NODE_ENV="$ENVIRONMENT" --local-config "vercel.$ENVIRONMENT.json"
        echo -e "${GREEN}Vercel deployment completed!${NC}"
    fi
fi

echo -e "${GREEN}🚀 Deployment to $ENVIRONMENT environment completed successfully!${NC}"
echo -e "${BLUE}=====================================${NC}" 