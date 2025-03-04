#!/bin/bash
# Consolidated Security Scanning Script
# Combines functionality from automated-security-scan.sh and security-scanning.sh
# Provides a unified interface for all security scanning operations

set -e

# Configuration
NAMESPACE="${NAMESPACE:-maily-production}"
REPORT_DIR="./security-reports"
AUTO_FIX="${AUTO_FIX:-false}"  # Whether to automatically fix non-critical issues
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"  # Set as environment variable
SEVERITY_THRESHOLD="${SEVERITY_THRESHOLD:-MEDIUM}"  # Minimum severity to report (LOW, MEDIUM, HIGH, CRITICAL)
SCAN_TYPE="${SCAN_TYPE:-all}"  # all, dependency, docker, code, secret, infrastructure, api
SCAN_TARGET="${SCAN_TARGET:-.}"
OUTPUT_DIR="${OUTPUT_DIR:-security-scan-results}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize report variables
report_id="security-scan-$(date +%Y%m%d-%H%M%S)"
report_file="${REPORT_DIR}/${report_id}.md"
critical_issues=0
high_issues=0
medium_issues=0
low_issues=0
auto_fixed=0

# Print header
print_header() {
  echo -e "${BLUE}=================================================="
  echo -e "          MAILY SECURITY SCAN SYSTEM           "
  echo -e "==================================================${NC}"
  echo ""
  echo -e "Scan type: ${SCAN_TYPE}"
  echo -e "Target: ${SCAN_TARGET}"
  echo -e "Severity threshold: ${SEVERITY_THRESHOLD}"
  echo -e "Report directory: ${REPORT_DIR}"
  echo -e "Auto-fix: ${AUTO_FIX}"
  echo ""
}

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

# Check dependencies
check_dependencies() {
  log "Checking dependencies..."

  missing_deps=()

  # Required tools
  for tool in kubectl jq git; do
    if ! command -v "${tool}" &> /dev/null; then
      missing_deps+=("${tool}")
    fi
  done

  # Optional tools
  optional_missing=()
  for tool in trivy sonarqube-scanner snyk zap-cli kube-bench kubesec popeye; do
    if ! command -v "${tool}" &> /dev/null; then
      optional_missing+=("${tool}")
    fi
  done

  if [ ${#missing_deps[@]} -gt 0 ]; then
    error "Missing required dependencies: ${missing_deps[*]}"
    error "Please install missing dependencies and try again"
    exit 1
  fi

  if [ ${#optional_missing[@]} -gt 0 ]; then
    warn "Missing optional tools: ${optional_missing[*]}"
    warn "Some scans may be skipped or limited"
  fi

  log "All required dependencies are installed"
}

# Create report directories
create_report_dirs() {
  # Create main report directory if it doesn't exist
  mkdir -p "${REPORT_DIR}"
  
  # Create scan-specific directories
  mkdir -p "${REPORT_DIR}/container-scans"
  mkdir -p "${REPORT_DIR}/dependency-scans"
  mkdir -p "${REPORT_DIR}/code-scans"
  mkdir -p "${REPORT_DIR}/secret-scans"
  mkdir -p "${REPORT_DIR}/infrastructure-scans"
  mkdir -p "${REPORT_DIR}/api-scans"
  
  log "Created report directories"
}

# Scan container images
scan_containers() {
  if [[ "${SCAN_TYPE}" != "all" && "${SCAN_TYPE}" != "docker" ]]; then
    log "Skipping container scanning"
    return 0
  fi

  log "Scanning container images..."

  # Get all images from Kubernetes
  image_list=$(kubectl get pods -n "${NAMESPACE}" -o json | jq -r '.items[].spec.containers[].image' 2>/dev/null | sort -u)
  if [ -z "${image_list}" ]; then
    warn "No container images found in namespace ${NAMESPACE}"
    return 0
  }

  log "Found $(echo "${image_list}" | wc -l | tr -d ' ') unique container images"

  # Create summary file
  echo "# Container Image Vulnerability Summary" > "${REPORT_DIR}/container-summary.md"
  echo "" >> "${REPORT_DIR}/container-summary.md"
  echo "| Image | Critical | High | Medium | Low |" >> "${REPORT_DIR}/container-summary.md"
  echo "|-------|----------|------|--------|-----|" >> "${REPORT_DIR}/container-summary.md"

  # Scan each image if trivy is available
  if command -v trivy &> /dev/null; then
    while read -r image; do
      if [ -z "${image}" ]; then
        continue
      fi

      log "Scanning image: ${image}"
      image_file_name=$(echo "${image}" | tr '/:' '_')

      # Run Trivy scan
      trivy image --format json --output "${REPORT_DIR}/container-scans/${image_file_name}.json" "${image}" || true
      # Generate text report for humans
      trivy image --severity "${SEVERITY_THRESHOLD}" --output "${REPORT_DIR}/container-scans/${image_file_name}.txt" "${image}" || true

      # Extract vulnerabilities by severity
      crit_count=$(jq -r '.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL") | .VulnerabilityID' "${REPORT_DIR}/container-scans/${image_file_name}.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      high_count=$(jq -r '.Results[].Vulnerabilities[] | select(.Severity=="HIGH") | .VulnerabilityID' "${REPORT_DIR}/container-scans/${image_file_name}.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      med_count=$(jq -r '.Results[].Vulnerabilities[] | select(.Severity=="MEDIUM") | .VulnerabilityID' "${REPORT_DIR}/container-scans/${image_file_name}.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      low_count=$(jq -r '.Results[].Vulnerabilities[] | select(.Severity=="LOW") | .VulnerabilityID' "${REPORT_DIR}/container-scans/${image_file_name}.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

      # Add to summary
      echo "| ${image} | ${crit_count} | ${high_count} | ${med_count} | ${low_count} |" >> "${REPORT_DIR}/container-summary.md"

      # Add to totals
      critical_issues=$((critical_issues + crit_count))
      high_issues=$((high_issues + high_count))
      medium_issues=$((medium_issues + med_count))
      low_issues=$((low_issues + low_count))
    done <<< "${image_list}"
  else
    warn "trivy not found, skipping container scanning"
  fi

  log "Container scan complete: ${critical_issues} critical, ${high_issues} high, ${medium_issues} medium, ${low_issues} low"
}

# Scan dependencies
scan_dependencies() {
  if [[ "${SCAN_TYPE}" != "all" && "${SCAN_TYPE}" != "dependency" ]]; then
    log "Skipping dependency scanning"
    return 0
  fi

  log "Scanning for dependency vulnerabilities..."

  # Scan Node.js dependencies
  if [ -f "${REPO_ROOT}/package.json" ]; then
    log "Scanning Node.js dependencies..."

    if command -v npm &> /dev/null; then
      # Run npm audit
      cd "${REPO_ROOT}"
      npm audit --json > "${REPORT_DIR}/dependency-scans/npm-audit.json" || true
      npm audit > "${REPORT_DIR}/dependency-scans/npm-audit.txt" || true

      # Parse results
      npm_crit=$(jq '.vulnerabilities[] | select(.severity == "critical") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      npm_high=$(jq '.vulnerabilities[] | select(.severity == "high") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      npm_med=$(jq '.vulnerabilities[] | select(.severity == "moderate") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      npm_low=$(jq '.vulnerabilities[] | select(.severity == "low") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

      log "Node.js dependencies: ${npm_crit} critical, ${npm_high} high, ${npm_med} moderate, ${npm_low} low"

      # Update totals
      critical_issues=$((critical_issues + npm_crit))
      high_issues=$((high_issues + npm_high))
      medium_issues=$((medium_issues + npm_med))
      low_issues=$((low_issues + npm_low))

      # Auto-fix if enabled and no critical vulnerabilities
      if [ "${AUTO_FIX}" = "true" ] && [ "${npm_crit}" -eq 0 ] && [ "${npm_high}" -eq 0 ]; then
        log "Automatically fixing non-critical NPM vulnerabilities..."
        npm audit fix --force > "${REPORT_DIR}/dependency-scans/npm-audit-fix.txt" 2>&1 || true
        auto_fixed=$((auto_fixed + 1))
      fi
    else
      warn "npm not found, skipping Node.js dependency scan"
    fi
  fi

  # Scan Python dependencies
  if [ -f "${REPO_ROOT}/requirements.txt" ]; then
    log "Scanning Python dependencies..."

    # Run safety check if available
    if command -v safety &> /dev/null; then
      safety check -r "${REPO_ROOT}/requirements.txt" --json > "${REPORT_DIR}/dependency-scans/python-safety.json" || true
      safety check -r "${REPO_ROOT}/requirements.txt" > "${REPORT_DIR}/dependency-scans/python-safety.txt" || true

      # Count issues
      py_issues=$(jq 'length' "${REPORT_DIR}/dependency-scans/python-safety.json" 2>/dev/null || echo "0")
      log "Python dependencies: ${py_issues} vulnerabilities found"
      
      # Add to medium issues (safety doesn't categorize by severity)
      medium_issues=$((medium_issues + py_issues))
    else
      warn "safety not found, skipping Python dependency scan"
    fi
  fi
}

# Scan for secrets in code
scan_secrets() {
  if [[ "${SCAN_TYPE}" != "all" && "${SCAN_TYPE}" != "secret" ]]; then
    log "Skipping secret scanning"
    return 0
  fi

  log "Scanning for secrets in code..."

  # Run gitleaks if available
  if command -v gitleaks &> /dev/null; then
    cd "${REPO_ROOT}"
    log "Running gitleaks to find secrets in the repository..."
    gitleaks detect --report-path "${REPORT_DIR}/secret-scans/gitleaks-report.json" --report-format json || true

    # Count secrets
    secrets_count=$(jq '. | length' "${REPORT_DIR}/secret-scans/gitleaks-report.json" 2>/dev/null || echo "0")
    log "Found ${secrets_count} potential secrets"
    
    # Add to high issues (secrets are always high risk)
    high_issues=$((high_issues + secrets_count))
  else
    warn "gitleaks not found, skipping secrets scan"
  fi
}

# Scan Kubernetes configuration
scan_infrastructure() {
  if [[ "${SCAN_TYPE}" != "all" && "${SCAN_TYPE}" != "infrastructure" ]]; then
    log "Skipping infrastructure scanning"
    return 0
  fi

  log "Scanning Kubernetes configuration..."

  # Run kube-bench
  if command -v kube-bench &> /dev/null; then
    log "Running kube-bench for CIS benchmark..."
    kube-bench --json | jq '.' > "${REPORT_DIR}/infrastructure-scans/kube-bench.json"
    kube-bench > "${REPORT_DIR}/infrastructure-scans/kube-bench.txt"

    # Parse results
    kb_fail=$(jq '.Controls[].Tests[].Results[] | select(.status == "FAIL") | .test_number' "${REPORT_DIR}/infrastructure-scans/kube-bench.json" | wc -l | tr -d ' ')
    kb_warn=$(jq '.Controls[].Tests[].Results[] | select(.status == "WARN") | .test_number' "${REPORT_DIR}/infrastructure-scans/kube-bench.json" | wc -l | tr -d ' ')
    kb_info=$(jq '.Controls[].Tests[].Results[] | select(.status == "INFO") | .test_number' "${REPORT_DIR}/infrastructure-scans/kube-bench.json" | wc -l | tr -d ' ')

    log "CIS benchmark results: ${kb_fail} failures, ${kb_warn} warnings, ${kb_info} info"
    
    # Add to issue counts
    high_issues=$((high_issues + kb_fail))
    medium_issues=$((medium_issues + kb_warn))
  else
    warn "kube-bench not found, skipping CIS benchmark scan"
  fi

  # Run kubesec
  if command -v kubesec &> /dev/null; then
    log "Running kubesec for security best practices..."

    # Get all deployments
    kubectl get deployments -n "${NAMESPACE}" -o json > "${REPORT_DIR}/infrastructure-scans/deployments.json"

    # Scan each deployment
    jq -r '.items[].metadata.name' "${REPORT_DIR}/infrastructure-scans/deployments.json" | while read -r deployment; do
      log "Scanning deployment: ${deployment}"
      kubectl get deployment "${deployment}" -n "${NAMESPACE}" -o yaml | kubesec scan - > "${REPORT_DIR}/infrastructure-scans/${deployment}-kubesec.json" || true
    done
  else
    warn "kubesec not found, skipping security best practices scan"
  fi

  # Run popeye
  if command -v popeye &> /dev/null; then
    log "Running popeye for Kubernetes cluster sanitization..."
    popeye --output json --namespace "${NAMESPACE}" > "${REPORT_DIR}/infrastructure-scans/popeye.json" || true
  else
    warn "popeye not found, skipping cluster sanitization scan"
  fi
}

# Scan API endpoints (OWASP ZAP)
scan_api() {
  if [[ "${SCAN_TYPE}" != "all" && "${SCAN_TYPE}" != "api" ]]; then
    log "Skipping API scanning"
    return 0
  fi

  log "Scanning API endpoints..."

  # Run OWASP ZAP if available
  if command -v zap-cli &> /dev/null; then
    API_URL="${API_URL:-}"
    
    if [ -z "${API_URL}" ]; then
      warn "No API_URL specified for ZAP scan"
      return 0
    fi
    
    log "Running ZAP scan against ${API_URL}..."
    zap-cli quick-scan --self-contained --spider --ajax-spider -r "${REPORT_DIR}/api-scans/zap-report.html" "${API_URL}" || true
    
    # Generate JSON report
    zap-cli report -o "${REPORT_DIR}/api-scans/zap-report.json" -f json || true
    
    # Count issues by severity
    zap_high=$(jq '.site[0].alerts[] | select(.riskcode == "3") | .instances' "${REPORT_DIR}/api-scans/zap-report.json" 2>/dev/null | jq 'length' | awk '{sum+=$1} END {print sum}' || echo "0")
    zap_med=$(jq '.site[0].alerts[] | select(.riskcode == "2") | .instances' "${REPORT_DIR}/api-scans/zap-report.json" 2>/dev/null | jq 'length' | awk '{sum+=$1} END {print sum}' || echo "0")
    zap_low=$(jq '.site[0].alerts[] | select(.riskcode == "1") | .instances' "${REPORT_DIR}/api-scans/zap-report.json" 2>/dev/null | jq 'length' | awk '{sum+=$1} END {print sum}' || echo "0")
    
    log "ZAP scan results: ${zap_high} high, ${zap_med} medium, ${zap_low} low"
    
    # Add to totals
    high_issues=$((high_issues + zap_high))
    medium_issues=$((medium_issues + zap_med))
    low_issues=$((low_issues + zap_low))
  else
    warn "zap-cli not found, skipping API scan"
  fi
}

# Generate security report
generate_report() {
  log "Generating security report..."

  # Create report header
  cat > "${report_file}" << EOF
# Security Scan Report

**Report ID:** ${report_id}
**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')
**Namespace:** ${NAMESPACE}
**Auto-fix Enabled:** ${AUTO_FIX}
**Scan Type:** ${SCAN_TYPE}

## Summary

| Severity  | Count | Description                  |
|-----------|-------|------------------------------|
| CRITICAL  | ${critical_issues} | Issues that must be fixed immediately |
| HIGH      | ${high_issues} | High priority security issues |
| MEDIUM    | ${medium_issues} | Medium risk security issues |
| LOW       | ${low_issues} | Low risk security issues |

**${auto_fixed}** issues were automatically fixed.

EOF

  # Add container scan results if performed
  if [[ "${SCAN_TYPE}" == "all" || "${SCAN_TYPE}" == "docker" ]]; then
    if [ -f "${REPORT_DIR}/container-summary.md" ]; then
      cat "${REPORT_DIR}/container-summary.md" >> "${report_file}"
    fi
  fi

  # Add Kubernetes security results if performed
  if [[ "${SCAN_TYPE}" == "all" || "${SCAN_TYPE}" == "infrastructure" ]]; then
    if [ -f "${REPORT_DIR}/infrastructure-scans/kube-bench.json" ]; then
      kb_fail=$(jq '.Controls[].Tests[].Results[] | select(.status == "FAIL") | .test_number' "${REPORT_DIR}/infrastructure-scans/kube-bench.json" | wc -l | tr -d ' ')
      kb_warn=$(jq '.Controls[].Tests[].Results[] | select(.status == "WARN") | .test_number' "${REPORT_DIR}/infrastructure-scans/kube-bench.json" | wc -l | tr -d ' ')
      kb_info=$(jq '.Controls[].Tests[].Results[] | select(.status == "INFO") | .test_number' "${REPORT_DIR}/infrastructure-scans/kube-bench.json" | wc -l | tr -d ' ')

      cat >> "${report_file}" << EOF

## CIS Kubernetes Benchmark

- Failures: ${kb_fail}
- Warnings: ${kb_warn}
- Info: ${kb_info}

See detailed report in \`${REPORT_DIR}/infrastructure-scans/kube-bench.txt\`

EOF
    fi
  fi

  # Add dependency scan results if performed
  if [[ "${SCAN_TYPE}" == "all" || "${SCAN_TYPE}" == "dependency" ]]; then
    if [ -f "${REPORT_DIR}/dependency-scans/npm-audit.json" ]; then
      npm_crit=$(jq '.vulnerabilities[] | select(.severity == "critical") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      npm_high=$(jq '.vulnerabilities[] | select(.severity == "high") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      npm_med=$(jq '.vulnerabilities[] | select(.severity == "moderate") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
      npm_low=$(jq '.vulnerabilities[] | select(.severity == "low") | .name' "${REPORT_DIR}/dependency-scans/npm-audit.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

      cat >> "${report_file}" << EOF

## Node.js Dependencies

- Critical: ${npm_crit}
- High: ${npm_high}
- Moderate: ${npm_med}
- Low: ${npm_low}

See detailed report in \`${REPORT_DIR}/dependency-scans/npm-audit.txt\`

EOF
    fi
  fi

  # Add secrets scan results if performed
  if [[ "${SCAN_TYPE}" == "all" || "${SCAN_TYPE}" == "secret" ]]; then
    if [ -f "${REPORT_DIR}/secret-scans/gitleaks-report.json" ]; then
      secrets_count=$(jq '. | length' "${REPORT_DIR}/secret-scans/gitleaks-report.json" 2>/dev/null || echo "0")

      cat >> "${report_file}" << EOF

## Secrets Detection

Found ${secrets_count} potential secrets in the codebase.

See detailed report in \`${REPORT_DIR}/secret-scans/gitleaks-report.json\`

EOF
    fi
  fi

  # Add API scan results if performed
  if [[ "${SCAN_TYPE}" == "all" || "${SCAN_TYPE}" == "api" ]]; then
    if [ -f "${REPORT_DIR}/api-scans/zap-report.json" ]; then
      zap_high=$(jq '.site[0].alerts[] | select(.riskcode == "3") | .instances' "${REPORT_DIR}/api-scans/zap-report.json" 2>/dev/null | jq 'length' | awk '{sum+=$1} END {print sum}' || echo "0")
      zap_med=$(jq '.site[0].alerts[] | select(.riskcode == "2") | .instances' "${REPORT_DIR}/api-scans/zap-report.json" 2>/dev/null | jq 'length' | awk '{sum+=$1} END {print sum}' || echo "0")
      zap_low=$(jq '.site[0].alerts[] | select(.riskcode == "1") | .instances' "${REPORT_DIR}/api-scans/zap-report.json" 2>/dev/null | jq 'length' | awk '{sum+=$1} END {print sum}' || echo "0")

      cat >> "${report_file}" << EOF

## API Security (ZAP)

- High: ${zap_high}
- Medium: ${zap_med}
- Low: ${zap_low}

See detailed report in \`${REPORT_DIR}/api-scans/zap-report.html\`

EOF
    fi
  fi

  # Add recommendations section
  cat >> "${report_file}" << EOF

## Recommendations

1. Address all CRITICAL and HIGH severity issues immediately
2. Schedule remediation for MEDIUM issues
3. Review LOW severity issues during regular maintenance
4. Update dependencies regularly
5. Implement automated security scanning in CI/CD pipeline

EOF

  # Add auto-fixed section if any issues were auto-fixed
  if [ "${auto_fixed}" -gt 0 ]; then
    cat >> "${report_file}" << EOF

## Auto-fixed Issues

${auto_fixed} issues were automatically fixed. See detailed fix logs in:

- \`${REPORT_DIR}/dependency-scans/npm-audit-fix.txt\`

EOF
  fi

  log "Report generated: ${report_file}"

  # Send notification if configured
  if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    send_notification
  fi
}

# Send Slack notification with report summary
send_notification() {
  log "Sending notification..."

  # Set color based on severity
  if [ "${critical_issues}" -gt 0 ]; then
    color="#FF0000" # Red for critical issues
  elif [ "${high_issues}" -gt 0 ]; then
    color="#FFA500" # Orange for high issues
  elif [ "${medium_issues}" -gt 0 ]; then
    color="#FFFF00" # Yellow for medium issues
  else
    color="#00FF00" # Green for no significant issues
  fi

  # Create notification payload
  payload=$(cat << EOF
{
  "attachments": [
    {
      "color": "${color}",
      "title": "Security Scan Report",
      "title_link": "${report_file}",
      "text": "Security scan completed with ${critical_issues} critical, ${high_issues} high, ${medium_issues} medium, and ${low_issues} low severity issues.",
      "fields": [
        {
          "title": "Critical Issues",
          "value": "${critical_issues}",
          "short": true
        },
        {
          "title": "High Issues",
          "value": "${high_issues}",
          "short": true
        },
        {
          "title": "Medium Issues",
          "value": "${medium_issues}",
          "short": true
        },
        {
          "title": "Low Issues",
          "value": "${low_issues}",
          "short": true
        }
      ],
      "footer": "Automated Security Scan",
      "footer_icon": "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/325/shield_1f6e1-fe0f.png",
      "ts": $(date +%s)
    }
  ]
}
EOF
)

  # Send notification
  curl -s -X POST -H "Content-Type: application/json" -d "${payload}" "${SLACK_WEBHOOK_URL}" > /dev/null
}

# Print usage information
usage() {
  cat << EOF
Maily Security Scan Script

Usage: $(basename "$0") [options]

Options:
  --scan-type TYPE       Type of scan to run (all, dependency, docker, code, secret, infrastructure, api)
  --namespace NS         Kubernetes namespace to scan (default: maily-production)
  --report-dir DIR       Directory to store reports (default: ./security-reports)
  --severity LEVEL       Minimum severity level to report (LOW, MEDIUM, HIGH, CRITICAL)
  --auto-fix             Automatically fix non-critical issues
  --output-dir DIR       Output directory (default: security-scan-results)
  --target DIR           Directory to scan (default: .)
  --api-url URL          API URL to scan
  --slack-webhook URL    Slack webhook URL for notifications
  --help                 Show this help message

Examples:
  $(basename "$0") --scan-type all
  $(basename "$0") --scan-type dependency --auto-fix
  $(basename "$0") --scan-type api --api-url https://api.example.com
EOF
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --scan-type)
        SCAN_TYPE="$2"
        shift 2
        ;;
      --namespace)
        NAMESPACE="$2"
        shift 2
        ;;
      --report-dir)
        REPORT_DIR="$2"
        shift 2
        ;;
      --severity)
        SEVERITY_THRESHOLD="$2"
        shift 2
        ;;
      --auto-fix)
        AUTO_FIX=true
        shift
        ;;
      --output-dir)
        OUTPUT_DIR="$2"
        shift 2
        ;;
      --target)
        SCAN_TARGET="$2"
        shift 2
        ;;
      --api-url)
        API_URL="$2"
        shift 2
        ;;
      --slack-webhook)
        SLACK_WEBHOOK_URL="$2"
        shift 2
        ;;
      --help)
        usage
        exit 0
        ;;
      *)
        error "Unknown option: $1"
        usage
        exit 1
        ;;
    esac
  done
}

# Main function
main() {
  # Parse command line arguments
  parse_args "$@"
  
  # Print header
  print_header
  
  # Check dependencies
  check_dependencies
  
  # Create report directories
  create_report_dirs
  
  # Run scans based on type
  scan_containers
  scan_dependencies
  scan_secrets
  scan_infrastructure
  scan_api
  
  # Generate final report
  generate_report
  
  # Return appropriate exit code
  if [ "${critical_issues}" -gt 0 ]; then
    error "Security scan completed with ${critical_issues} critical issues"
    exit 1
  elif [ "${high_issues}" -gt 0 ]; then
    warn "Security scan completed with ${high_issues} high severity issues"
    exit 0
  else
    log "Security scan completed successfully"
    exit 0
  fi
}

# Run main function with all arguments
main "$@"
