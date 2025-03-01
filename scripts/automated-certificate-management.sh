#!/bin/bash

# Automated Certificate Management Script
#
# This script automates TLS certificate management by:
# 1. Checking certificate expiration dates across environments
# 2. Triggering proactive renewals for certificates nearing expiration
# 3. Validating certificate configuration and chain
# 4. Generating reports on certificate status
# 5. Notifying of any certificate issues
#
# Can be scheduled to run daily to replace manual certificate management

set -e

# Configuration
NAMESPACE="${NAMESPACE:-maily-production}"
RENEWAL_THRESHOLD_DAYS="${RENEWAL_THRESHOLD_DAYS:-30}" # Renew certs with less than this many days remaining
CRITICAL_THRESHOLD_DAYS="${CRITICAL_THRESHOLD_DAYS:-14}" # Critical alert if less than this many days remaining
REPORT_DIR="./certificate-reports"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}" # Set as environment variable
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-}" # Set as environment variable

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialize report variables
report_id="cert-status-$(date +%Y%m%d-%H%M%S)"
report_file="${REPORT_DIR}/${report_id}.md"
cert_status=()
cert_issues=()
renewals_triggered=0
errors=0

# Logging functions
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
  cert_status+=("✅ $1")
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
  cert_status+=("⚠️ WARNING: $1")
  cert_issues+=("⚠️ $1")
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
  cert_status+=("❌ ERROR: $1")
  cert_issues+=("❌ $1")
  errors=$((errors + 1))
}

# Create report directory if it doesn't exist
mkdir -p "${REPORT_DIR}"

# Check if kubectl is available
check_dependencies() {
  if ! command -v kubectl &> /dev/null; then
    error "kubectl command not found. Please install kubectl and ensure it's in your PATH."
    exit 1
  fi

  # Check if openssl is available
  if ! command -v openssl &> /dev/null; then
    error "openssl command not found. Please install openssl and ensure it's in your PATH."
    exit 1
  }

  # Check if we can access the cluster
  if ! kubectl get nodes &> /dev/null; then
    error "Cannot access Kubernetes cluster. Please check your kubeconfig."
    exit 1
  }
}

# Get certificate resources from Kubernetes
get_certificates() {
  log "Getting certificate resources from cluster..."

  # Get cert-manager Certificate resources
  kubectl get certificate -n "${NAMESPACE}" -o json > "${report_file}.certificates.json"

  # Count certificates
  cert_count=$(jq '.items | length' "${report_file}.certificates.json")
  log "Found ${cert_count} certificate resources"

  # Get TLS secrets
  kubectl get secrets -n "${NAMESPACE}" --field-selector type=kubernetes.io/tls -o json > "${report_file}.tls_secrets.json"

  # Count TLS secrets
  secret_count=$(jq '.items | length' "${report_file}.tls_secrets.json")
  log "Found ${secret_count} TLS secrets"
}

# Check certificate expiration dates
check_expiry() {
  log "Checking certificate expiration dates..."

  # Get current timestamp in seconds since epoch
  now=$(date +%s)

  # Process all TLS secrets
  jq -r '.items[] | .metadata.name' "${report_file}.tls_secrets.json" | while read -r secret_name; do
    log "Checking TLS secret: ${secret_name}"

    # Extract certificate from secret
    kubectl get secret "${secret_name}" -n "${NAMESPACE}" -o jsonpath='{.data.tls\.crt}' | base64 -d > "${report_file}.${secret_name}.crt"

    # Get certificate details
    cert_info=$(openssl x509 -in "${report_file}.${secret_name}.crt" -noout -text)

    # Get expiry date
    expiry_date=$(openssl x509 -in "${report_file}.${secret_name}.crt" -noout -enddate | cut -d= -f2)
    expiry_timestamp=$(date -d "${expiry_date}" +%s)

    # Calculate days until expiry
    seconds_until_expiry=$((expiry_timestamp - now))
    days_until_expiry=$((seconds_until_expiry / 86400))

    # Get issuer
    issuer=$(openssl x509 -in "${report_file}.${secret_name}.crt" -noout -issuer)

    # Get domains (Subject Alternative Names)
    sans=$(openssl x509 -in "${report_file}.${secret_name}.crt" -noout -text | grep -A1 "Subject Alternative Name" | tail -n1 | sed 's/DNS://g; s/, /\n/g' | tr -d ' ')

    # Record certificate details
    echo "### ${secret_name}" >> "${report_file}.cert_details"
    echo "- **Expires in:** ${days_until_expiry} days (${expiry_date})" >> "${report_file}.cert_details"
    echo "- **Issuer:** ${issuer}" >> "${report_file}.cert_details"
    echo "- **Domains:**" >> "${report_file}.cert_details"
    echo "${sans}" | while read -r domain; do
      echo "  - ${domain}" >> "${report_file}.cert_details"
    done
    echo "" >> "${report_file}.cert_details"

    # Check if certificate needs renewal
    if [ "${days_until_expiry}" -lt "${CRITICAL_THRESHOLD_DAYS}" ]; then
      error "Certificate ${secret_name} expires in ${days_until_expiry} days (CRITICAL)"
    elif [ "${days_until_expiry}" -lt "${RENEWAL_THRESHOLD_DAYS}" ]; then
      warn "Certificate ${secret_name} expires in ${days_until_expiry} days (WARNING)"
    else
      log "Certificate ${secret_name} expires in ${days_until_expiry} days (OK)"
    fi

    # Clean up temp file
    rm "${report_file}.${secret_name}.crt"
  done
}

# Validate certificate chains
validate_certificates() {
  log "Validating certificate chains..."

  # Process all TLS secrets
  jq -r '.items[] | .metadata.name' "${report_file}.tls_secrets.json" | while read -r secret_name; do
    # Extract certificate from secret
    kubectl get secret "${secret_name}" -n "${NAMESPACE}" -o jsonpath='{.data.tls\.crt}' | base64 -d > "${report_file}.${secret_name}.crt"
    kubectl get secret "${secret_name}" -n "${NAMESPACE}" -o jsonpath='{.data.ca\.crt}' | base64 -d > "${report_file}.${secret_name}.ca.crt" 2>/dev/null || true

    # Check if we have a CA certificate
    if [ -s "${report_file}.${secret_name}.ca.crt" ]; then
      # Verify certificate against CA
      if openssl verify -CAfile "${report_file}.${secret_name}.ca.crt" "${report_file}.${secret_name}.crt" > /dev/null 2>&1; then
        log "Certificate ${secret_name} has a valid chain"
      else
        warn "Certificate ${secret_name} has chain validation issues"
      fi
    else
      # No CA certificate, just check the certificate itself
      if openssl x509 -in "${report_file}.${secret_name}.crt" -noout > /dev/null 2>&1; then
        log "Certificate ${secret_name} is valid"
      else
        error "Certificate ${secret_name} is invalid"
      fi
    fi

    # Clean up temp files
    rm -f "${report_file}.${secret_name}.crt" "${report_file}.${secret_name}.ca.crt"
  done
}

# Trigger certificate renewals
trigger_renewals() {
  log "Checking for certificates that need renewal..."

  # Get current timestamp in seconds since epoch
  now=$(date +%s)

  # Process all cert-manager certificates
  jq -r '.items[] | .metadata.name' "${report_file}.certificates.json" | while read -r cert_name; do
    # Get cert-manager Certificate resource
    cert_json=$(jq ".items[] | select(.metadata.name == \"${cert_name}\")" "${report_file}.certificates.json")

    # Get secret name from Certificate resource
    secret_name=$(echo "${cert_json}" | jq -r '.spec.secretName')

    # Extract certificate from secret
    kubectl get secret "${secret_name}" -n "${NAMESPACE}" -o jsonpath='{.data.tls\.crt}' | base64 -d > "${report_file}.${secret_name}.crt"

    # Get expiry date
    expiry_date=$(openssl x509 -in "${report_file}.${secret_name}.crt" -noout -enddate | cut -d= -f2)
    expiry_timestamp=$(date -d "${expiry_date}" +%s)

    # Calculate days until expiry
    seconds_until_expiry=$((expiry_timestamp - now))
    days_until_expiry=$((seconds_until_expiry / 86400))

    # Trigger renewal if needed
    if [ "${days_until_expiry}" -lt "${RENEWAL_THRESHOLD_DAYS}" ]; then
      log "Triggering renewal for certificate ${cert_name} (expires in ${days_until_expiry} days)"

      # Annotate the Certificate resource to trigger renewal
      kubectl annotate certificate "${cert_name}" -n "${NAMESPACE}" cert-manager.io/renew="true" --overwrite

      renewals_triggered=$((renewals_triggered + 1))
    fi

    # Clean up temp file
    rm "${report_file}.${secret_name}.crt"
  done

  log "Triggered renewal for ${renewals_triggered} certificates"
}

# Generate certificate status report
generate_report() {
  log "Generating certificate status report..."

  # Create report header
  cat > "${report_file}" << EOF
# Certificate Status Report

**Report ID:** ${report_id}
**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')
**Namespace:** ${NAMESPACE}
**Renewal Threshold:** ${RENEWAL_THRESHOLD_DAYS} days
**Critical Threshold:** ${CRITICAL_THRESHOLD_DAYS} days

## Summary
- Total certificates checked: $(jq '.items | length' "${report_file}.tls_secrets.json")
- Certificates renewed: ${renewals_triggered}
- Issues found: ${#cert_issues[@]}

EOF

  # Add certificate status entries
  echo -e "## Status Log\n" >> "${report_file}"
  for status in "${cert_status[@]}"; do
    echo "- ${status}" >> "${report_file}"
  done

  # Add certificate issues if any
  if [ ${#cert_issues[@]} -gt 0 ]; then
    echo -e "\n## Issues\n" >> "${report_file}"
    for issue in "${cert_issues[@]}"; do
      echo "- ${issue}" >> "${report_file}"
    done
  fi

  # Add certificate details
  if [ -f "${report_file}.cert_details" ]; then
    echo -e "\n## Certificate Details\n" >> "${report_file}"
    cat "${report_file}.cert_details" >> "${report_file}"
    rm "${report_file}.cert_details"
  fi

  log "Report generated: ${report_file}"

  # Clean up temporary files
  rm -f "${report_file}.certificates.json" "${report_file}.tls_secrets.json"

  # Send notification if configured
  if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    send_slack_notification
  fi

  # Send email if configured
  if [ -n "${EMAIL_RECIPIENT}" ]; then
    send_email_notification
  fi
}

# Send Slack notification
send_slack_notification() {
  log "Sending Slack notification..."

  # Set notification color based on presence of issues
  if [ "${errors}" -gt 0 ]; then
    color="#FF0000" # Red for errors
  elif [ "${#cert_issues[@]}" -gt 0 ]; then
    color="#FFA500" # Orange for warnings
  else
    color="#36a64f" # Green for OK
  fi

  # Create notification payload
  payload=$(cat << EOF
{
  "attachments": [
    {
      "color": "${color}",
      "title": "Certificate Status Report",
      "text": "Report ID: ${report_id}",
      "fields": [
        {
          "title": "Certificates Checked",
          "value": "$(jq '.items | length' "${report_file}.tls_secrets.json")",
          "short": true
        },
        {
          "title": "Certificates Renewed",
          "value": "${renewals_triggered}",
          "short": true
        },
        {
          "title": "Issues Found",
          "value": "${#cert_issues[@]}",
          "short": true
        }
      ]
    }
  ]
}
EOF
)

  # Send notification
  curl -s -X POST -H "Content-Type: application/json" -d "${payload}" "${SLACK_WEBHOOK_URL}" > /dev/null
}

# Send email notification
send_email_notification() {
  log "Sending email notification..."

  # Set email subject based on presence of issues
  if [ "${errors}" -gt 0 ]; then
    subject="[CRITICAL] Certificate Status Report - ${errors} critical issues"
  elif [ "${#cert_issues[@]}" -gt 0 ]; then
    subject="[WARNING] Certificate Status Report - ${#cert_issues[@]} issues"
  else
    subject="[OK] Certificate Status Report"
  fi

  # Send email with report attached
  if command -v mail &> /dev/null; then
    mail -s "${subject}" "${EMAIL_RECIPIENT}" < "${report_file}"
  else
    log "Mail command not found, skipping email notification"
  fi
}

# Main function
main() {
  log "Starting automated certificate management..."

  # Check dependencies
  check_dependencies

  # Get certificates
  get_certificates

  # Check expiry dates
  check_expiry

  # Validate certificates
  validate_certificates

  # Trigger renewals if needed
  trigger_renewals

  # Generate report
  generate_report

  # Return appropriate exit code
  if [ "${errors}" -gt 0 ]; then
    error "Certificate management completed with ${errors} errors"
    exit 1
  else
    log "Certificate management completed successfully"
    exit 0
  fi
}

# Run main function
main
