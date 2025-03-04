#!/bin/bash
#
# Automated Rollback Mechanism
#
# This script provides an automated rollback mechanism for deployments
# It works with ArgoCD to revert to previous stable versions when issues are detected
# Features:
# - Automated rollback decisions based on health metrics
# - Previous version identification
# - Rollback execution and verification
# - Notifications

set -e

# Configuration
ENVIRONMENT="${1:-production}"
APP_NAME="maily-${ENVIRONMENT}"
ARGOCD_SERVER="${ARGOCD_SERVER:-https://argocd.maily.example.com}"
NAMESPACE="maily-${ENVIRONMENT}"
PROMETHEUS_ENDPOINT="${PROMETHEUS_ENDPOINT:-http://prometheus.maily.example.com}"
VERIFICATION_TIMEOUT=300 # 5 minutes
MAX_RETRIES=3
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

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
}

# Function to check system health and determine if rollback is needed
check_health() {
  log "Checking system health for ${APP_NAME}..."

  # Check ArgoCD app health
  health=$(argocd app get "${APP_NAME}" --server "${ARGOCD_SERVER}" -o json | jq -r '.status.health.status')
  if [[ "${health}" != "Healthy" ]]; then
    warn "ArgoCD app health is ${health}, not Healthy"
    return 1
  fi

  # Check pod status
  failing_pods=$(kubectl get pods -n "${NAMESPACE}" -o json | jq -r '[.items[] | select(.status.phase != "Running" and .status.phase != "Succeeded")] | length')
  if [[ "${failing_pods}" -gt 0 ]]; then
    warn "Found ${failing_pods} failing pods in ${NAMESPACE}"
    return 1
  fi

  # Check error rate
  error_rate=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query?query=sum(rate(http_requests_total{namespace=\"${NAMESPACE}\",status=~\"5..\"}[5m]))/sum(rate(http_requests_total{namespace=\"${NAMESPACE}\"}[5m]))" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")

  # Convert scientific notation to decimal if needed
  if [[ "${error_rate}" =~ e ]]; then
    error_rate=$(printf "%.4f" "${error_rate}")
  fi

  # Check if error rate is acceptable (below 2%)
  if (( $(echo "${error_rate} > 0.02" | bc -l) )); then
    warn "Error rate is too high: ${error_rate} (> 2%)"
    return 1
  fi

  # Check API latency
  latency=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query?query=histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket{namespace=\"${NAMESPACE}\"}[5m]))by(le))" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")

  # Convert scientific notation to decimal if needed
  if [[ "${latency}" =~ e ]]; then
    latency=$(printf "%.4f" "${latency}")
  fi

  # Check if latency is acceptable (below 1s)
  if (( $(echo "${latency} > 1.0" | bc -l) )); then
    warn "P95 latency is too high: ${latency}s (> 1s)"
    return 1
  fi

  log "All health checks passed"
  return 0
}

# Function to get previous stable version
get_previous_version() {
  log "Finding previous stable version..."

  # Get ArgoCD application history
  history=$(argocd app history "${APP_NAME}" --server "${ARGOCD_SERVER}" -o json)

  # Find the previous deployed version (second most recent)
  previous_version=$(echo "${history}" | jq -r 'sort_by(.id) | reverse | .[1].revision' 2>/dev/null)

  if [[ -z "${previous_version}" || "${previous_version}" == "null" ]]; then
    warn "Could not find previous version, will use 'HEAD^' as fallback"
    previous_version="HEAD^"
  fi

  log "Previous version identified: ${previous_version}"
  echo "${previous_version}"
}

# Function to execute rollback
execute_rollback() {
  local version="$1"
  log "Executing rollback to version: ${version}"

  retry_count=0
  while [ ${retry_count} -lt ${MAX_RETRIES} ]; do
    # Attempt rollback
    if [[ "${version}" =~ ^[0-9]+$ ]]; then
      # Rollback to a specific ArgoCD application revision
      if argocd app rollback "${APP_NAME}" "${version}" --server "${ARGOCD_SERVER}"; then
        log "Rollback initiated successfully"
        break
      fi
    else
      # Set to a specific Git revision
      if argocd app set "${APP_NAME}" --revision "${version}" --server "${ARGOCD_SERVER}"; then
        argocd app sync "${APP_NAME}" --server "${ARGOCD_SERVER}"
        log "Rollback to Git revision ${version} initiated successfully"
        break
      fi
    fi

    # If we get here, rollback failed
    retry_count=$((retry_count + 1))
    if [ ${retry_count} -lt ${MAX_RETRIES} ]; then
      warn "Rollback attempt ${retry_count} failed, retrying in 5 seconds..."
      sleep 5
    else
      error "Rollback failed after ${MAX_RETRIES} attempts"
      return 1
    fi
  done

  return 0
}

# Function to verify rollback was successful
verify_rollback() {
  log "Verifying rollback success..."

  timeout_counter=0
  retry_interval=10
  max_timeout=$((VERIFICATION_TIMEOUT / retry_interval))

  while [ ${timeout_counter} -lt ${max_timeout} ]; do
    # Check ArgoCD sync and health status
    app_status=$(argocd app get "${APP_NAME}" --server "${ARGOCD_SERVER}" -o json)
    sync_status=$(echo "${app_status}" | jq -r '.status.sync.status')
    health_status=$(echo "${app_status}" | jq -r '.status.health.status')

    log "Current status: Sync=${sync_status}, Health=${health_status}"

    if [[ "${sync_status}" == "Synced" && "${health_status}" == "Healthy" ]]; then
      # Double-check with our health function
      if check_health; then
        log "Rollback verified successfully!"
        return 0
      fi
    fi

    timeout_counter=$((timeout_counter + 1))
    if [ ${timeout_counter} -lt ${max_timeout} ]; then
      log "Waiting for rollback to stabilize (${timeout_counter}/${max_timeout})..."
      sleep ${retry_interval}
    else
      error "Rollback verification timed out after ${VERIFICATION_TIMEOUT} seconds"
      return 1
    fi
  done

  return 1
}

# Function to send notifications
send_notification() {
  local status="$1"
  local details="$2"

  if [[ -z "${SLACK_WEBHOOK_URL}" ]]; then
    log "No Slack webhook configured, skipping notification"
    return 0
  fi

  log "Sending rollback notification..."

  # Construct emoji based on status
  if [[ "${status}" == "success" ]]; then
    emoji="✅"
  else
    emoji="❌"
  fi

  # Create notification payload
  payload=$(cat << EOF
{
  "text": "${emoji} Automated Rollback: ${status^^}",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "${emoji} Automated Rollback: ${status^^}"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Environment:* ${ENVIRONMENT}"
        },
        {
          "type": "mrkdwn",
          "text": "*Application:* ${APP_NAME}"
        },
        {
          "type": "mrkdwn",
          "text": "*Timestamp:* $(date '+%Y-%m-%d %H:%M:%S')"
        },
        {
          "type": "mrkdwn",
          "text": "*Triggered By:* CI/CD Pipeline"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Details:*\n${details}"
      }
    }
  ]
}
EOF
)

  # Send notification
  curl -s -X POST -H "Content-Type: application/json" -d "${payload}" "${SLACK_WEBHOOK_URL}" > /dev/null
}

# Main function
main() {
  log "Starting automated rollback mechanism for ${APP_NAME}..."

  # Parse command line arguments
  ROLLBACK_FORCED=false
  VERSION=""

  while getopts "e:fv:" opt; do
    case ${opt} in
      e)
        ENVIRONMENT=$OPTARG
        APP_NAME="maily-${ENVIRONMENT}"
        NAMESPACE="maily-${ENVIRONMENT}"
        ;;
      f)
        ROLLBACK_FORCED=true
        ;;
      v)
        VERSION=$OPTARG
        ;;
      \?)
        error "Invalid option: -$OPTARG"
        exit 1
        ;;
    esac
  done

  rollback_needed=false

  # Check if rollback is needed
  if [[ "${ROLLBACK_FORCED}" == "true" ]]; then
    log "Rollback forced via command line argument"
    rollback_needed=true
  else
    if ! check_health; then
      log "Health check failed, rollback needed"
      rollback_needed=true
    else
      log "System is healthy, no rollback needed"
      exit 0
    fi
  fi

  if [[ "${rollback_needed}" == "true" ]]; then
    # Get previous version if not specified
    if [[ -z "${VERSION}" ]]; then
      VERSION=$(get_previous_version)
    fi

    # Execute rollback
    if execute_rollback "${VERSION}"; then
      # Verify rollback
      if verify_rollback; then
        log "Rollback completed successfully"
        send_notification "success" "Successfully rolled back to version: ${VERSION}"
        exit 0
      else
        error "Rollback verification failed"
        send_notification "failure" "Rollback verification failed for version: ${VERSION}"
        exit 1
      fi
    else
      error "Rollback execution failed"
      send_notification "failure" "Failed to execute rollback to version: ${VERSION}"
      exit 1
    fi
  fi
}

# Run main function
main "$@"
