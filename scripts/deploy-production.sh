#!/bin/bash
set -e

# Maily Production Deployment Script
# This script handles the complete deployment process for Maily
# It manages environment setup, database migrations, and Vercel deployment

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Maily Production Deployment${NC}"
echo "Timestamp: $(date)"

# Check required tools
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Error: jq is required but not installed. Aborting.${NC}"; exit 1; }
command -v vercel >/dev/null 2>&1 || { echo -e "${RED}Error: Vercel CLI is required but not installed. Aborting.${NC}"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}Error: kubectl is required but not installed. Aborting.${NC}"; exit 1; }

# Load environment variables
if [ -f "config/.env.production" ]; then
    echo -e "${GREEN}Loading production environment variables...${NC}"
    export $(grep -v '^#' config/.env.production | xargs)
else
    echo -e "${RED}Error: config/.env.production file not found${NC}"
    exit 1
fi

# Validate required environment variables
REQUIRED_VARS=("DATABASE_URL" "REDIS_URL" "API_URL" "JWT_SECRET" "VERCEL_TOKEN" "POLYGON_RPC_URL")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: Required environment variable ${var} is not set${NC}"
        exit 1
    fi
done

# Run database migrations
run_migrations() {
    echo -e "${GREEN}Running database migrations...${NC}"
    
    # Check database connection
    DATABASE_URL=${DATABASE_URL} node -e "
        const { Client } = require('pg');
        const client = new Client({
            connectionString: process.env.DATABASE_URL
        });
        client.connect()
            .then(() => {
                console.log('Database connection successful');
                client.end();
            })
            .catch(err => {
                console.error('Database connection failed:', err);
                process.exit(1);
            });
    " || { echo -e "${RED}Error: Database connection failed. Aborting deployment.${NC}"; exit 1; }
    
    # Run SQL migrations
    echo "Running SQL migrations..."
    cd migrations/sql
    for sql_file in $(find . -name "*.sql" | sort); do
        echo "Applying migration: $sql_file"
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f $sql_file || { 
            echo -e "${RED}Error: Failed to apply migration $sql_file${NC}"
            exit 1
        }
    done
    cd ../..
    
    # Run Prisma migrations if needed
    if [ -f "prisma/schema.prisma" ]; then
        echo "Running Prisma migrations..."
        npx prisma migrate deploy || { 
            echo -e "${RED}Error: Prisma migration failed${NC}"
            exit 1
        }
    fi
    
    echo -e "${GREEN}Database migrations completed successfully${NC}"
}

# Deploy backend services to Kubernetes
deploy_backend() {
    echo -e "${GREEN}Deploying backend services to Kubernetes...${NC}"
    
    # Check kubectl connection
    kubectl get nodes > /dev/null || { 
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    }
    
    # Deploy Redis cache first (dependency)
    echo "Deploying Redis..."
    kubectl apply -f kubernetes/deployments/redis.yaml
    kubectl rollout status deployment/redis
    
    # Deploy API service with canary deployment
    echo "Deploying API service with canary deployment..."
    kubectl apply -f kubernetes/deployments/maily-api.yaml --record=true
    kubectl rollout pause deployment/maily-api
    
    # Scale to ensure we have capacity for both versions during transition
    kubectl scale deployment/maily-api --replicas=2
    
    # Update image for canary pods
    kubectl set image deployment/maily-api maily-api=maily-api:latest --record=true
    
    # Resume rollout to allow canary pods to be created
    kubectl rollout resume deployment/maily-api
    
    # Deploy AI service
    echo "Deploying AI service..."
    kubectl apply -f kubernetes/deployments/ai-mesh-deployment.yaml --record=true
    
    # Check deployment status
    echo "Waiting for deployments to be ready..."
    kubectl rollout status deployment/maily-api
    kubectl rollout status deployment/ai-mesh
    
    echo -e "${YELLOW}Letting services stabilize for 30 minutes...${NC}"
    echo "Started stabilization period at: $(date)"
    
    # Allow manual continuation to speed up development deployments
    echo "Press Ctrl+C to interrupt stabilization period (NOT RECOMMENDED FOR PRODUCTION)"
    sleep 1800 || echo -e "${YELLOW}Stabilization period interrupted.${NC}"
    
    echo "Finished stabilization period at: $(date)"
    echo -e "${GREEN}Backend services deployed successfully${NC}"
}

# Deploy frontend to Vercel
deploy_frontend() {
    echo -e "${GREEN}Deploying frontend to Vercel...${NC}"
    
    # Build web app
    echo "Building web app..."
    npm run build:web || { 
        echo -e "${RED}Error: Frontend build failed${NC}"
        exit 1
    }
    
    # Deploy to Vercel
    echo "Deploying to Vercel..."
    cd apps/web
    vercel deploy --prod --token=${VERCEL_TOKEN} || { 
        echo -e "${RED}Error: Vercel deployment failed${NC}"
        exit 1
    }
    cd ../..
    
    echo -e "${GREEN}Frontend deployed successfully${NC}"
}

# Setup monitoring
setup_monitoring() {
    echo -e "${GREEN}Setting up monitoring...${NC}"
    
    # Deploy Prometheus
    echo "Deploying Prometheus..."
    kubectl apply -f kubernetes/monitoring/prometheus-production.yaml
    
    # Deploy Grafana
    echo "Deploying Grafana..."
    kubectl apply -f kubernetes/monitoring/grafana-production.yaml
    
    # Deploy the monitoring ingress
    echo "Setting up monitoring ingress..."
    kubectl apply -f kubernetes/monitoring/ingress.yaml
    
    # Apply Datadog configuration for lightweight monitoring
    echo "Configuring Datadog..."
    kubectl apply -f kubernetes/monitoring/datadog-values.yaml
    
    echo -e "${GREEN}Monitoring setup completed${NC}"
}

# Run stress tests
run_stress_tests() {
    echo -e "${YELLOW}Running stress tests...${NC}"
    
    # Email sending capacity test
    echo "Testing email sending capacity..."
    ./scripts/testing/load-testing/consolidated-load-test.sh --test-type email --users 100 --duration 30 || {
        echo -e "${YELLOW}Warning: Email sending test did not meet performance targets${NC}"
    }
    
    # Canvas concurrent users test
    echo "Testing canvas with 10 simultaneous users..."
    ./scripts/testing/load-testing/consolidated-load-test.sh --test-type canvas --users 10 --duration 60 || {
        echo -e "${YELLOW}Warning: Canvas performance test did not meet targets${NC}"
    }
    
    # AI agent responsiveness test
    echo "Testing AI agent responsiveness..."
    python tests/performance/test_ai_agent_responsiveness.py || {
        echo -e "${YELLOW}Warning: AI agent responsiveness test did not meet targets${NC}"
    }
    
    # Blockchain verification test
    echo "Testing blockchain verification throughput..."
    ./scripts/testing/load-testing/consolidated-load-test.sh --test-type blockchain --operations 100 || {
        echo -e "${YELLOW}Warning: Blockchain verification test did not meet performance targets${NC}"
    }
    
    echo -e "${GREEN}Stress tests completed${NC}"
}

# Main deployment flow
main() {
    echo "Starting deployment process..."
    
    # Process command line arguments
    MIGRATE_ONLY=false
    SERVICES_ONLY=false
    FRONTEND_ONLY=false
    
    for arg in "$@"; do
        case $arg in
            --migrate-only)
                MIGRATE_ONLY=true
                ;;
            --services-only)
                SERVICES_ONLY=true
                ;;
            --frontend-only)
                FRONTEND_ONLY=true
                ;;
        esac
    done
    
    # If specific flags are provided, run only those components
    if [ "$MIGRATE_ONLY" = true ]; then
        echo "Running migrations only mode..."
        run_migrations
        echo -e "${GREEN}Migration-only deployment completed successfully!${NC}"
        exit 0
    fi
    
    if [ "$SERVICES_ONLY" = true ]; then
        echo "Running services only mode..."
        deploy_backend
        setup_monitoring
        echo -e "${GREEN}Services-only deployment completed successfully!${NC}"
        exit 0
    fi
    
    if [ "$FRONTEND_ONLY" = true ]; then
        echo "Running frontend only mode..."
        deploy_frontend
        echo -e "${GREEN}Frontend-only deployment completed successfully!${NC}"
        exit 0
    fi
    
    # If no specific flags are provided, run the complete deployment
    run_migrations
    deploy_backend
    deploy_frontend
    setup_monitoring
    
    # Run stress tests if --test flag is provided
    if [[ "$*" == *"--test"* ]]; then
        run_stress_tests
    fi
    
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo "Timestamp: $(date)"
    
    # Output service URLs
    echo -e "${GREEN}Service URLs:${NC}"
    echo "Frontend: https://maily.vercel.app"
    echo "API: https://api.maily.example.com"
    echo "Monitoring: https://monitor.maily.example.com"
}

# Execute main function with all arguments
main "$@"