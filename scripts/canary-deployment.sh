#!/bin/bash
#
# Canary Deployment Script
#
# This script manages canary deployments with traffic splitting and verification
# It works with ArgoCD and Kubernetes to provide progressive rollouts

set -e

# Configuration
ENVIRONMENT="${1:-staging}"
CANARY_PERCENTAGE="${2:-10}"
DEPLOYMENT_ID="${3:-canary-$(date +%Y%m%d%H%M%S)-${GITHUB_SHA:0:7}}"
ARGOCD_SERVER="${ARGOCD_SERVER:-https://argocd.maily.example.com}"
APP_NAME="maily-${ENVIRONMENT}"
NAMESPACE="maily-${ENVIRONMENT}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
  exit 1
}

# Function to check if ArgoCD is available
check_argocd() {
  log "Checking ArgoCD connection..."
  if ! argocd version --client; then
    error "ArgoCD CLI not found or not working"
  fi

  # Check ArgoCD connection
  if ! argocd app list --server "${ARGOCD_SERVER}" > /dev/null 2>&1; then
    error "Cannot connect to ArgoCD server at ${ARGOCD_SERVER}"
  fi

  log "ArgoCD connection successful"
}

# Function to deploy canary version
deploy_canary() {
  log "Deploying canary version to ${ENVIRONMENT} with ${CANARY_PERCENTAGE}% traffic..."

  # Update application to enable canary with specified percentage
  argocd app patch "${APP_NAME}" \
    --server "${ARGOCD_SERVER}" \
    --patch "{\"spec\":{\"source\":{\"helm\":{\"parameters\":[{\"name\":\"canary.enabled\",\"value\":\"true\"}, {\"name\":\"canary.percentage\",\"value\":\"${CANARY_PERCENTAGE}\"}, {\"name\":\"canary.deploymentId\",\"value\":\"${DEPLOYMENT_ID}\"}]}}}}" \
    --type merge

  # Sync the application to apply changes
  argocd app sync "${APP_NAME}" --server "${ARGOCD_SERVER}"

  log "Canary deployment ${DEPLOYMENT_ID} initiated"
  echo "${DEPLOYMENT_ID}" > canary-deployment-id.txt
}

# Function to wait for deployment to stabilize
wait_for_deployment() {
  log "Waiting for canary deployment to stabilize..."

  timeout=300
  counter=0
  while [ ${counter} -lt ${timeout} ]; do
    # Check if application is healthy
    health=$(argocd app get "${APP_NAME}" --server "${ARGOCD_SERVER}" -o json | jq -r '.status.health.status')
    sync_status=$(argocd app get "${APP_NAME}" --server "${ARGOCD_SERVER}" -o json | jq -r '.status.sync.status')

    if [[ "${health}" == "Healthy" && "${sync_status}" == "Synced" ]]; then
      log "Deployment is healthy and synced"
      return 0
    fi

    counter=$((counter + 5))
    log "Waiting for deployment to stabilize (${counter}/${timeout}s)..."
    sleep 5
  done

  error "Timeout waiting for deployment to stabilize"
}

# Function to promote canary to full deployment
promote_canary() {
  log "Promoting canary to full deployment..."

  # Update application to disable canary
  argocd app patch "${APP_NAME}" \
    --server "${ARGOCD_SERVER}" \
    --patch "{\"spec\":{\"source\":{\"helm\":{\"parameters\":[{\"name\":\"canary.enabled\",\"value\":\"false\"}]}}}}" \
    --type merge

  # Sync the application to apply changes
  argocd app sync "${APP_NAME}" --server "${ARGOCD_SERVER}"

  # Wait for deployment to stabilize
  wait_for_deployment

  log "Canary promotion completed"
}

# Function to rollback canary deployment
rollback_canary() {
  log "Rolling back canary deployment..."

  # Update application to disable canary
  argocd app patch "${APP_NAME}" \
    --server "${ARGOCD_SERVER}" \
    --patch "{\"spec\":{\"source\":{\"helm\":{\"parameters\":[{\"name\":\"canary.enabled\",\"value\":\"false\"}]}}}}" \
    --type merge

  # Sync the application to apply changes
  argocd app sync "${APP_NAME}" --server "${ARGOCD_SERVER}"

  # Wait for rollback to stabilize
  wait_for_deployment

  log "Canary rollback completed"
}

# Main function
main() {
  # Parse command line arguments
  while getopts "e:p:d:a:r" opt; do
    case ${opt} in
      e)
        ENVIRONMENT=$OPTARG
        ;;
      p)
        CANARY_PERCENTAGE=$OPTARG
        ;;
      d)
        DEPLOYMENT_ID=$OPTARG
        ;;
      a)
        ACTION=$OPTARG
        ;;
      r)
        ROLLBACK=true
        ;;
      \?)
        error "Invalid option: -$OPTARG"
        ;;
    esac
  done

  # Check ArgoCD
  check_argocd

  # Determine action
  if [[ "${ROLLBACK}" == "true" ]]; then
    rollback_canary
  elif [[ "${ACTION}" == "promote" ]]; then
    promote_canary
  else
    deploy_canary
    wait_for_deployment
  fi
}

# Run main function
main "$@"
