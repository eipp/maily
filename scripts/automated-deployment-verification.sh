u#!/bin/bash

# Automated Deployment Verification Script
#
# This script automates the verification process after deployments by:
# 1. Checking pod status in Kubernetes
# 2. Verifying health endpoints for all services
# 3. Running smoke tests
# 4. Checking metrics for anomalies after deployment
# 5. Generating a verification report
#
# It can be integrated into CI/CD pipelines to replace manual verification steps

set -e

# Configuration
NAMESPACE="maily-production"
SERVICES=("maily-api" "maily-web" "maily-worker")
API_HEALTH_ENDPOINT="https://api.maily.example.com/health"
WEB_HEALTH_ENDPOINT="https://app.maily.example.com/api/health"
WORKER_HEALTH_ENDPOINT="https://workers.maily.example.com/health"
VERIFICATION_TIMEOUT=300 # 5 minutes
PROMETHEUS_ENDPOINT="http://prometheus.maily.example.com"
REPORT_DIR="./deployment-reports"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}" # Set as environment variable

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialize report variables
verification_passed=true
verification_results=()

# Logging functions
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
  verification_results+=("✅ $1")
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
  verification_results+=("⚠️ WARNING: $1")
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
  verification_results+=("❌ ERROR: $1")
  verification_passed=false
}

# Create report directory if it doesn't exist
mkdir -p "${REPORT_DIR}"

# Generate a unique report ID
report_id="deploy-verify-$(date +%Y%m%d-%H%M%S)"
report_file="${REPORT_DIR}/${report_id}.md"

# Verify Kubernetes pods
verify_pods() {
  log "Verifying Kubernetes pods in namespace ${NAMESPACE}..."

  # Get pod statuses
  pod_output=$(kubectl get pods -n "${NAMESPACE}" -o json)

  # Count total, running, and failed pods
  total_pods=$(echo "${pod_output}" | jq '.items | length')
  running_pods=$(echo "${pod_output}" | jq '[.items[] | select(.status.phase == "Running")] | length')
  failed_pods=$(echo "${pod_output}" | jq '[.items[] | select(.status.phase == "Failed" or .status.phase == "CrashLoopBackOff")] | length')

  log "Found ${total_pods} total pods, ${running_pods} running, ${failed_pods} failed"

  # Check for failed pods
  if [ "${failed_pods}" -gt 0 ]; then
    error "Found ${failed_pods} failed pods in namespace ${NAMESPACE}"

    # Get details of failed pods
    failed_pod_names=$(echo "${pod_output}" | jq -r '.items[] | select(.status.phase == "Failed" or .status.phase == "CrashLoopBackOff") | .metadata.name')

    for pod in ${failed_pod_names}; do
      error "Failed pod: ${pod}"
      kubectl describe pod "${pod}" -n "${NAMESPACE}" >> "${report_file}.pod-details"
      kubectl logs "${pod}" -n "${NAMESPACE}" --tail=100 >> "${report_file}.pod-logs"
    done
  fi

  # Check if all pods are running
  if [ "${running_pods}" -ne "${total_pods}" ]; then
    warn "Not all pods are in Running state (${running_pods}/${total_pods})"
  else
    log "All pods are in Running state"
  fi
}

# Verify service health endpoints
verify_health_endpoints() {
  log "Verifying service health endpoints..."

  # Function to check a health endpoint
  check_endpoint() {
    local service=$1
    local endpoint=$2
    local retry_count=0
    local max_retries=5
    local success=false

    while [ ${retry_count} -lt ${max_retries} ] && [ "${success}" = "false" ]; do
      response=$(curl -s -o /dev/null -w "%{http_code}" "${endpoint}" || echo "000")

      if [ "${response}" = "200" ]; then
        log "${service} health check passed (HTTP 200)"
        success=true
      else
        retry_count=$((retry_count + 1))
        if [ ${retry_count} -lt ${max_retries} ]; then
          warn "${service} health check failed (HTTP ${response}), retrying in 5 seconds..."
          sleep 5
        else
          error "${service} health check failed after ${max_retries} attempts (HTTP ${response})"
        fi
      fi
    done
  }

  # Check each service's health endpoint
  check_endpoint "API" "${API_HEALTH_ENDPOINT}"
  check_endpoint "Web" "${WEB_HEALTH_ENDPOINT}"
  check_endpoint "Worker" "${WORKER_HEALTH_ENDPOINT}"
}

# Run smoke tests
run_smoke_tests() {
  log "Running smoke tests..."

  smoke_test_output=$(pnpm test:smoke 2>&1) || {
    error "Smoke tests failed"
    echo "${smoke_test_output}" >> "${report_file}.smoke-tests"
    return 1
  }

  log "Smoke tests passed"
  echo "${smoke_test_output}" >> "${report_file}.smoke-tests"
}

# Check metrics for anomalies
check_metrics() {
  log "Checking metrics for anomalies..."

  # Check error rate
  error_rate=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query?query=sum(rate(http_requests_total{job=~\"maily-.*\",status=~\"5..\"}[5m]))/sum(rate(http_requests_total{job=~\"maily-.*\"}[5m]))" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")

  # Convert scientific notation to decimal if needed
  if [[ "${error_rate}" =~ e ]]; then
    error_rate=$(printf "%.4f" "${error_rate}")
  fi

  # Check if error rate is acceptable (below 1%)
  if (( $(echo "${error_rate} > 0.01" | bc -l) )); then
    error "Error rate is too high: ${error_rate} (> 1%)"
  else
    log "Error rate is acceptable: ${error_rate} (< 1%)"
  fi

  # Check latency
  p95_latency=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query?query=histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket{job=~\"maily-.*\"}[5m]))by(le))" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")

  # Convert scientific notation to decimal if needed
  if [[ "${p95_latency}" =~ e ]]; then
    p95_latency=$(printf "%.4f" "${p95_latency}")
  fi

  # Check if latency is acceptable (below 500ms)
  if (( $(echo "${p95_latency} > 0.5" | bc -l) )); then
    warn "P95 latency is high: ${p95_latency}s (> 500ms)"
  else
    log "P95 latency is acceptable: ${p95_latency}s (< 500ms)"
  fi

  # Check CPU and memory usage
  resource_output=$(curl -s "${PROMETHEUS_ENDPOINT}/api/v1/query?query=sum(container_cpu_usage_seconds_total{namespace=\"${NAMESPACE}\",container!=\"POD\",container!=\"\"})by(container)" | jq '.data.result' 2>/dev/null || echo "[]")

  echo "Resource utilization data captured in report"
  echo "${resource_output}" >> "${report_file}.metrics"
}

# Generate verification report
generate_report() {
  log "Generating verification report..."

  # Create report header
  cat > "${report_file}" << EOF
# Deployment Verification Report

**Report ID:** ${report_id}
**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')
**Status:** ${verification_passed:+"✅ PASSED":-"❌ FAILED"}

## Verification Steps

EOF

  # Add verification results
  for result in "${verification_results[@]}"; do
    echo "- ${result}" >> "${report_file}"
  done

  # Add additional sections
  if [ -f "${report_file}.pod-details" ]; then
    echo -e "\n## Failed Pods Details\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.pod-details" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.pod-details"
  fi

  if [ -f "${report_file}.pod-logs" ]; then
    echo -e "\n## Failed Pods Logs\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.pod-logs" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.pod-logs"
  fi

  if [ -f "${report_file}.smoke-tests" ]; then
    echo -e "\n## Smoke Tests Output\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.smoke-tests" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.smoke-tests"
  fi

  if [ -f "${report_file}.metrics" ]; then
    echo -e "\n## Metrics Data\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.metrics" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.metrics"
  fi

  log "Report generated: ${report_file}"

  # Send notification if configured
  if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    send_notification
  fi
}

# Send notification with report summary
send_notification() {
  log "Sending notification..."

  # Create a simplified report for the notification
  notification_title="Deployment Verification: ${verification_passed:+"✅ PASSED":-"❌ FAILED"}"

  # Create notification payload
  payload=$(cat << EOF
{
  "text": "${notification_title}",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "${notification_title}"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Report ID:* ${report_id}\n*Timestamp:* $(date '+%Y-%m-%d %H:%M:%S')"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "$(head -n 10 "${report_file}" | grep -v "#" | grep -v "Report ID" | grep -v "Timestamp" | grep -v "Status")\n..."
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "See full report for details: ${REPORT_DIR}/${report_id}.md"
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
  log "Starting automated deployment verification..."

  # Run verification steps
  verify_pods
  verify_health_endpoints
  run_smoke_tests
  check_metrics

  # Generate report
  generate_report

  # Return appropriate exit code
  if [ "${verification_passed}" = "true" ]; then
    log "Deployment verification PASSED!"
    exit 0
  else
    error "Deployment verification FAILED!"
    exit 1
  fi
}

# Run main function
main
