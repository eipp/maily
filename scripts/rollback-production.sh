#!/bin/bash
set -e

# Maily Production Rollback Script
# This script handles emergency rollbacks for all Maily services

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}Starting Maily EMERGENCY ROLLBACK${NC}"
echo "Timestamp: $(date)"

# Check required tools
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}Error: kubectl is required but not installed. Aborting.${NC}"; exit 1; }
command -v vercel >/dev/null 2>&1 || { echo -e "${RED}Error: Vercel CLI is required but not installed. Aborting.${NC}"; exit 1; }

# Load environment variables if needed
if [ -f ".env.production" ]; then
    echo -e "${GREEN}Loading production environment variables...${NC}"
    export $(grep -v '^#' .env.production | xargs)
fi

# Rollback Kubernetes deployments
rollback_kubernetes() {
    echo -e "${YELLOW}Rolling back Kubernetes deployments...${NC}"
    
    # Check kubectl connection
    kubectl get nodes > /dev/null || { 
        echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
        exit 1
    }
    
    # Rollback API service
    echo "Rolling back API service..."
    kubectl rollout undo deployment/maily-api
    
    # Rollback AI service
    echo "Rolling back AI service..."
    kubectl rollout undo deployment/ai-mesh
    
    # Rollback email service if it exists
    if kubectl get deployment email-service &>/dev/null; then
        echo "Rolling back email service..."
        kubectl rollout undo deployment/email-service
    fi
    
    # Check rollback status
    echo "Waiting for rollbacks to complete..."
    kubectl rollout status deployment/maily-api
    kubectl rollout status deployment/ai-mesh
    
    echo -e "${GREEN}Kubernetes rollbacks completed successfully${NC}"
}

# Rollback Vercel frontend
rollback_frontend() {
    echo -e "${YELLOW}Rolling back Vercel frontend deployment...${NC}"
    
    # Execute Vercel rollback
    cd apps/web
    vercel rollback --project=maily-web -y || {
        echo -e "${RED}Vercel rollback failed. Try manually with:${NC}"
        echo "vercel rollback --project=maily-web"
        echo "vercel rollback --project=maily-web --scope=your-team"
    }
    cd ../..
    
    echo -e "${GREEN}Frontend rollback completed${NC}"
}

# Clear Redis caches if needed
clear_caches() {
    echo -e "${YELLOW}Clearing Redis caches...${NC}"
    
    if [ -z "$REDIS_URL" ]; then
        echo -e "${RED}REDIS_URL not set, skipping cache clearing${NC}"
        return
    fi
    
    # Extract Redis host and port from URL
    REDIS_HOST=$(echo $REDIS_URL | sed -E 's/^redis:\/\/([^:]+):.*/\1/')
    REDIS_PORT=$(echo $REDIS_URL | sed -E 's/^redis:\/\/[^:]+:([0-9]+).*/\1/')
    
    if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PORT" ]; then
        echo -e "${RED}Could not parse Redis host/port, skipping cache clearing${NC}"
        return
    fi
    
    # Clear specific cache keys
    echo "Clearing verification and certificate caches..."
    redis-cli -h $REDIS_HOST -p $REDIS_PORT KEYS "blockchain:verification:*" | xargs redis-cli -h $REDIS_HOST -p $REDIS_PORT DEL
    redis-cli -h $REDIS_HOST -p $REDIS_PORT KEYS "canvas:*:certificate" | xargs redis-cli -h $REDIS_HOST -p $REDIS_PORT DEL
    redis-cli -h $REDIS_HOST -p $REDIS_PORT KEYS "verification_data:*" | xargs redis-cli -h $REDIS_HOST -p $REDIS_PORT DEL
    
    echo -e "${GREEN}Cache clearing completed${NC}"
}

# Notify team about the rollback
notify_team() {
    echo -e "${YELLOW}Notifying team about emergency rollback...${NC}"
    
    # In a real environment, this would send emails, Slack messages, etc.
    # For now, we'll just create a local log file
    
    LOGFILE="rollback_$(date +%Y%m%d_%H%M%S).log"
    
    echo "EMERGENCY ROLLBACK EXECUTED" > $LOGFILE
    echo "Timestamp: $(date)" >> $LOGFILE
    echo "Executed by: $(whoami)" >> $LOGFILE
    echo "Reason: $1" >> $LOGFILE
    echo "Services affected:" >> $LOGFILE
    echo "- API Service" >> $LOGFILE
    echo "- AI Service" >> $LOGFILE
    echo "- Frontend" >> $LOGFILE
    
    echo -e "${GREEN}Team notification created: $LOGFILE${NC}"
    echo "Please send this log file to the team and create an incident report."
}

# Main rollback flow
main() {
    echo "Starting emergency rollback process..."
    
    # Get reason for rollback
    REASON=${1:-"Unknown issue requiring emergency rollback"}
    
    # Confirm rollback
    read -p "Are you sure you want to perform an EMERGENCY ROLLBACK? This will revert all services to their previous versions. (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Rollback cancelled${NC}"
        exit 1
    fi
    
    # Perform rollbacks
    rollback_kubernetes
    rollback_frontend
    clear_caches
    notify_team "$REASON"
    
    echo -e "${GREEN}Emergency rollback completed successfully!${NC}"
    echo "Timestamp: $(date)"
    echo -e "${YELLOW}IMPORTANT: Create an incident report in the team's incident management system.${NC}"
}

# Execute main function with reason as the first argument
main "$1"