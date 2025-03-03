#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}  MAILY PRODUCTION DEPLOYMENT PLAN  ${NC}"
echo -e "${GREEN}====================================${NC}"
echo "Started at: $(date)"
echo

# Extract credentials from config/.env.production
if [ -f "config/.env.production" ]; then
    echo "Extracting API keys from config/.env.production"
    DATADOG_API_KEY=$(grep -v '^#' config/.env.production | grep DATADOG_API_KEY | cut -d'=' -f2)
    DATADOG_APP_KEY=$(grep -v '^#' config/.env.production | grep DATADOG_APP_KEY | cut -d'=' -f2)
    VERCEL_TOKEN=$(grep -v '^#' config/.env.production | grep VERCEL_TOKEN | cut -d'=' -f2)
    
    # Validate extracted keys
    if [ -z "$DATADOG_API_KEY" ] || [ -z "$DATADOG_APP_KEY" ] || [ -z "$VERCEL_TOKEN" ]; then
        echo -e "${YELLOW}Warning: One or more API keys not found in config/.env.production${NC}"
        # Keep placeholders for missing keys
        [ -z "$DATADOG_API_KEY" ] && DATADOG_API_KEY="[insert your actual key]"
        [ -z "$DATADOG_APP_KEY" ] && DATADOG_APP_KEY="[insert your actual key]"
        [ -z "$VERCEL_TOKEN" ] && VERCEL_TOKEN="[insert your actual token]"
    fi
else
    echo -e "${YELLOW}Warning: config/.env.production not found for API key extraction${NC}"
    DATADOG_API_KEY="[insert your actual key]"
    DATADOG_APP_KEY="[insert your actual key]"
    VERCEL_TOKEN="[insert your actual token]"
fi

# Set environment variables
export DATADOG_API_KEY
export DATADOG_APP_KEY
export VERCEL_TOKEN

echo -e "${YELLOW}Step 1: Loading environment variables from config/.env.production${NC}"
if [ -f "config/.env.production" ]; then
    echo "Loading all variables from config/.env.production"
    export $(grep -v '^#' config/.env.production | xargs)
else
    echo -e "${RED}Error: config/.env.production file not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 2: Verifying kubectl configuration${NC}"
echo "Setting kubectl context to production cluster"
kubectl config use-context "arn:aws:eks:us-east-1:178967885703:cluster/maily-production-cluster"

echo "Verifying existing deployments"
kubectl get deployments

echo
echo -e "${YELLOW}Step 3: Deployment Sequence${NC}"

# 1. Run migrations
echo -e "${GREEN}STAGE 1: Running migrations ($(date))${NC}"
./scripts/deploy-production.sh --migrate-only

echo -e "${YELLOW}Waiting 10 minutes for verification...${NC}"
echo "Started verification wait at: $(date)"
sleep 600
echo "Completed verification wait at: $(date)"

# 2. Deploy backend services
echo -e "${GREEN}STAGE 2: Deploying services ($(date))${NC}"
./scripts/deploy-production.sh --services-only

echo -e "${YELLOW}Waiting 30 minutes for stabilization...${NC}"
echo "Started stabilization wait at: $(date)"
sleep 1800
echo "Completed stabilization wait at: $(date)"

# 3. Deploy frontend
echo -e "${GREEN}STAGE 3: Deploying frontend ($(date))${NC}"
./scripts/deploy-production.sh --frontend-only

echo -e "${GREEN}Deployment sequence completed successfully!${NC}"

echo
echo -e "${YELLOW}Step 4: Running Validation Checks${NC}"

echo "Running critical metrics script"
./scripts/check-critical-metrics.sh

echo "Checking for pods in error state"
kubectl get pods -o wide | grep -i error

echo "Verifying frontend health"
curl -s https://maily.vercel.app/health

echo "Verifying API health"
curl -s https://api.maily.example.com/health

echo
echo -e "${YELLOW}Step 5: Post-Deployment Monitoring${NC}"
echo "Monitoring Datadog dashboard for 1 hour post-deployment"
echo "Started monitoring at: $(date)"
echo "Focus on blockchain verification rate and AI service latency"
echo "ALERT THRESHOLDS:"
echo "- Blockchain verification success rate < 95% → execute rollback"
echo "- AI service p95 latency > 5000ms for >10 minutes → execute rollback"

# Function to check blockchain verification rate
check_blockchain_verification() {
    local rate=$(curl -s -X GET "https://api.datadoghq.eu/api/v1/query?from=$(date -d '10 minutes ago' +%s)&to=$(date +%s)&query=sum:maily.blockchain.verification.success{*}.as_count()/sum:maily.blockchain.verification.total{*}.as_count()*100" \
        -H "DD-API-KEY: ${DATADOG_API_KEY}" \
        -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" | jq -r '.series[0].pointlist[-1][1]')
    
    if (( $(echo "$rate < 95" | bc -l) )); then
        echo -e "${RED}ALERT: Blockchain verification rate at ${rate}% (below 95% threshold)${NC}"
        return 1
    else
        echo -e "${GREEN}Blockchain verification rate: ${rate}% (above 95% threshold)${NC}"
        return 0
    fi
}

# Function to check AI service latency
check_ai_latency() {
    local latency=$(curl -s -X GET "https://api.datadoghq.eu/api/v1/query?from=$(date -d '10 minutes ago' +%s)&to=$(date +%s)&query=p95:maily.ai.response.time{*}" \
        -H "DD-API-KEY: ${DATADOG_API_KEY}" \
        -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" | jq -r '.series[0].pointlist[-1][1]')
    
    if (( $(echo "$latency > 5000" | bc -l) )); then
        echo -e "${RED}ALERT: AI service p95 latency at ${latency}ms (above 5000ms threshold)${NC}"
        return 1
    else
        echo -e "${GREEN}AI service p95 latency: ${latency}ms (below 5000ms threshold)${NC}"
        return 0
    fi
}

# Monitor for 1 hour (in 5-minute intervals)
echo "Beginning 1-hour monitoring cycle..."
for i in {1..12}; do
    echo "Monitoring cycle $i of 12..."
    
    # Check blockchain verification
    if ! check_blockchain_verification; then
        echo -e "${RED}CRITICAL: Blockchain verification below threshold, initiating rollback...${NC}"
        ./scripts/rollback-production.sh
        exit 1
    fi
    
    # Check AI latency
    if ! check_ai_latency; then
        # If latency is high, check for 2 more cycles (10 minutes total)
        echo -e "${YELLOW}WARNING: AI latency above threshold, monitoring for persistence...${NC}"
        sleep 300
        if ! check_ai_latency; then
            sleep 300
            if ! check_ai_latency; then
                echo -e "${RED}CRITICAL: AI latency persistently high for >10 minutes, initiating rollback...${NC}"
                ./scripts/rollback-production.sh
                exit 1
            fi
        fi
    fi
    
    # Wait 5 minutes before next check
    if [ $i -lt 12 ]; then
        echo "Waiting 5 minutes until next check..."
        sleep 300
    fi
done

echo
echo -e "${GREEN}Deployment of new Trust Infrastructure completed${NC}"
echo "Key features implemented:"
echo "- Transaction batching"
echo "- Parallel verification workflows"
echo "- Memory caching"
echo
echo -e "${RED}IMPORTANT: Special attention required for blockchain metrics during first few hours${NC}"
echo
echo "Deployment script completed at: $(date)" 