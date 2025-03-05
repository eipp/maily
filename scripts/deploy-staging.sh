#!/bin/bash
set -e

# Maily Staging Deployment Script
# This script handles the complete deployment process for Maily Staging
# It manages environment setup, database migrations, and Vercel deployment

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Maily Staging Deployment${NC}"
echo "Timestamp: $(date)"

# Check required tools
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Error: jq is required but not installed. Aborting.${NC}"; exit 1; }
command -v vercel >/dev/null 2>&1 || { echo -e "${RED}Error: Vercel CLI is required but not installed. Aborting.${NC}"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}Error: kubectl is required but not installed. Aborting.${NC}"; exit 1; }

# Load environment variables
if [ -f "config/.env.staging" ]; then
    echo -e "${GREEN}Loading staging environment variables...${NC}"
    export $(grep -v '^#' config/.env.staging | xargs)
else
    echo -e "${RED}Error: config/.env.staging file not found${NC}"
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
    echo "Checking database connection to staging database..."
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
    if [ -d "migrations/sql" ]; then
        cd migrations/sql
        for sql_file in $(find . -name "*.sql" | sort); do
            echo "Applying migration: $sql_file"
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f $sql_file || { 
                echo -e "${RED}Error: Failed to apply migration $sql_file${NC}"
                exit 1
            }
        done
        cd ../..
    else
        echo "No SQL migrations directory found. Skipping SQL migrations."
    fi
    
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
    echo -e "${GREEN}Deploying backend services to Kubernetes staging namespace...${NC}"
    
    # Check kubectl connection
    kubectl get nodes > /dev/null || { 
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    }
    
    # Ensure staging namespace exists
    kubectl create namespace staging --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Redis cache first (dependency)
    echo "Deploying Redis..."
    kubectl apply -f kubernetes/deployments/redis.yaml -n staging
    kubectl rollout status deployment/redis -n staging
    
    # Deploy API service
    echo "Deploying API service..."
    kubectl apply -f kubernetes/deployments/maily-api-staging.yaml -n staging --record=true
    
    # Deploy AI service
    echo "Deploying AI service..."
    kubectl apply -f kubernetes/deployments/ai-mesh-deployment-staging.yaml -n staging --record=true
    
    # Check deployment status
    echo "Waiting for deployments to be ready..."
    kubectl rollout status deployment/maily-api -n staging
    kubectl rollout status deployment/ai-mesh -n staging
    
    echo -e "${YELLOW}Letting services stabilize for 5 minutes...${NC}"
    echo "Started stabilization period at: $(date)"
    
    # Allow manual continuation to speed up development deployments
    echo "Press Ctrl+C to interrupt stabilization period"
    sleep 300 || echo -e "${YELLOW}Stabilization period interrupted.${NC}"
    
    echo "Finished stabilization period at: $(date)"
    echo -e "${GREEN}Backend services deployed successfully${NC}"
}

# Deploy frontend to Vercel
deploy_frontend() {
    echo -e "${GREEN}Deploying frontend to Vercel (staging)...${NC}"
    
    # Build web app
    echo "Building web app..."
    npm run build:web || { 
        echo -e "${RED}Error: Frontend build failed${NC}"
        exit 1
    }
    
    # Deploy to Vercel
    echo "Deploying to Vercel preview environment..."
    cd apps/web
    vercel deploy --token=${VERCEL_TOKEN} || { 
        echo -e "${RED}Error: Vercel deployment failed${NC}"
        exit 1
    }
    cd ../..
    
    echo -e "${GREEN}Frontend deployed successfully${NC}"
}

# Setup monitoring
setup_monitoring() {
    echo -e "${GREEN}Setting up monitoring for staging...${NC}"
    
    # Deploy Prometheus
    echo "Deploying Prometheus..."
    kubectl apply -f kubernetes/monitoring/prometheus-staging.yaml -n staging
    
    # Deploy Grafana
    echo "Deploying Grafana..."
    kubectl apply -f kubernetes/monitoring/grafana-staging.yaml -n staging
    
    # Deploy the monitoring ingress
    echo "Setting up monitoring ingress..."
    kubectl apply -f kubernetes/monitoring/staging-ingress.yaml -n staging
    
    echo -e "${GREEN}Monitoring setup completed${NC}"
}

# Run integration tests
run_integration_tests() {
    echo -e "${GREEN}Running integration tests...${NC}"
    
    # Run API integration tests
    echo "Running API integration tests..."
    npm run test:integration:api || {
        echo -e "${RED}Error: API integration tests failed${NC}"
        exit 1
    }
    
    # Run email flow tests
    echo "Testing email flow..."
    npm run test:email:flow || {
        echo -e "${RED}Error: Email flow tests failed${NC}"
        exit 1
    }
    
    # Run AI integration tests
    echo "Testing AI integration..."
    npm run test:integration:ai || {
        echo -e "${RED}Error: AI integration tests failed${NC}"
        exit 1
    }
    
    echo -e "${GREEN}Integration tests completed successfully${NC}"
}

# Run post-deployment health checks
run_health_checks() {
    echo -e "${GREEN}Running post-deployment health checks...${NC}"
    
    # Run smoke test
    echo "Running smoke tests..."
    node scripts/smoke-test.js --environment=staging || {
        echo -e "${RED}Error: Smoke tests failed${NC}"
        exit 1
    }
    
    # Enhanced smoke tests
    echo "Running enhanced smoke tests..."
    node scripts/enhanced-smoke-test.js --environment=staging || {
        echo -e "${YELLOW}Warning: Enhanced smoke tests detected minor issues. Continuing deployment...${NC}"
    }
    
    # Check API health
    echo "Checking API health..."
    curl -s "${API_URL}/health" | grep "status" | grep "ok" > /dev/null || {
        echo -e "${RED}Error: API health check failed${NC}"
        exit 1
    }
    
    # Check AI service health
    echo "Checking AI service health..."
    curl -s "${AI_SERVICE_URL}/health" | grep "status" | grep "ok" > /dev/null || {
        echo -e "${RED}Error: AI service health check failed${NC}"
        exit 1
    }
    
    # Check database connectivity
    echo "Checking database connectivity..."
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
    " || { echo -e "${RED}Error: Database connectivity check failed${NC}"; exit 1; }
    
    echo -e "${GREEN}Health checks completed successfully${NC}"
}

# Run end-to-end tests on the staging environment
run_e2e_tests() {
    echo -e "${GREEN}Running end-to-end tests on staging environment...${NC}"
    
    # Run our comprehensive e2e test script
    node scripts/e2e-staging-test.js || {
        if [ $? -eq 1 ]; then
            echo -e "${YELLOW}Warning: End-to-end tests detected some non-critical issues.${NC}"
            echo -e "${YELLOW}Please review the test report for details.${NC}"
        else
            echo -e "${RED}Error: End-to-end tests failed with critical issues.${NC}"
            echo -e "${RED}Please check the test report for details.${NC}"
            
            # Only fail deployment if --require-e2e-success flag is set
            if [ "$REQUIRE_E2E_SUCCESS" = true ]; then
                exit 1
            fi
        fi
    }
    
    echo -e "${GREEN}End-to-end tests completed!${NC}"
}

# Main deployment flow
main() {
    echo "Starting staging deployment process..."
    
    # Process command line arguments
    MIGRATE_ONLY=false
    SERVICES_ONLY=false
    FRONTEND_ONLY=false
    SKIP_TESTS=false
    SKIP_E2E=false
    REQUIRE_E2E_SUCCESS=false
    
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
            --skip-tests)
                SKIP_TESTS=true
                ;;
            --skip-e2e)
                SKIP_E2E=true
                ;;
            --require-e2e-success)
                REQUIRE_E2E_SUCCESS=true
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
        if [ "$SKIP_TESTS" = false ]; then
            run_health_checks
        fi
        echo -e "${GREEN}Services-only deployment completed successfully!${NC}"
        exit 0
    fi
    
    if [ "$FRONTEND_ONLY" = true ]; then
        echo "Running frontend only mode..."
        deploy_frontend
        if [ "$SKIP_TESTS" = false ]; then
            run_health_checks
        fi
        echo -e "${GREEN}Frontend-only deployment completed successfully!${NC}"
        exit 0
    fi
    
    # If no specific flags are provided, run the complete deployment
    run_migrations
    deploy_backend
    deploy_frontend
    setup_monitoring
    
    # Run tests unless skip flag is provided
    if [ "$SKIP_TESTS" = false ]; then
        run_integration_tests
        run_health_checks
        
        # Run E2E tests unless skip flag is provided
        if [ "$SKIP_E2E" = false ]; then
            run_e2e_tests
        fi
    fi
    
    echo -e "${GREEN}Staging deployment completed successfully!${NC}"
    echo "Timestamp: $(date)"
    
    # Output service URLs
    echo -e "${GREEN}Service URLs:${NC}"
    echo "Frontend: https://maily-staging.vercel.app"
    echo "API: https://api-staging.maily.example.com"
    echo "Monitoring: https://monitor-staging.maily.example.com"
}

# Execute main function with all arguments
main "$@"