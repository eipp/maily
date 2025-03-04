#!/bin/sh
# Script to update references to relocated scripts in CI/CD pipelines and other configuration files
# Simplified version that works with any POSIX-compliant shell

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODE="report"
TARGET="."

# Logging functions
log() {
  echo "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
  echo "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
  echo "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

# Print header
print_header() {
  echo "${BLUE}=================================================="
  echo "          SCRIPT REFERENCE UPDATER           "
  echo "==================================================${NC}"
  echo ""
  echo "Mode: ${MODE}"
  echo "Target: ${TARGET}"
  echo ""
}

# Find references to old script paths in files
find_script_references() {
  log "Scanning files in ${TARGET} for script references..."
  
  # Find all text files, excluding binary files, .git, node_modules, and other irrelevant directories
  find "${TARGET}" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" -not -path "*/build/*" \
    -not -name "*.png" -not -name "*.jpg" -not -name "*.jpeg" -not -name "*.gif" -not -name "*.ico" \
    -not -name "*.woff" -not -name "*.woff2" -not -name "*.ttf" -not -name "*.eot" -not -name "*.svg" \
    -not -name "*.pdf" -not -name "*.exe" -not -name "*.dll" -not -name "*.so" -not -name "*.dylib" \
    -exec grep -l "scripts/" {} \; 2>/dev/null || true
}

# Generate mapping file
generate_mapping_file() {
  local mapping_file="$1"
  
  # Core deployment scripts
  echo "scripts/maily-deploy.sh|scripts/core/maily-deploy.sh" > "$mapping_file"
  echo "scripts/deployment-validator.sh|scripts/core/deployment-validator.sh" >> "$mapping_file"
  echo "scripts/config-collector.sh|scripts/core/config-collector.sh" >> "$mapping_file"
  echo "scripts/update-image-tags.sh|scripts/core/update-image-tags.sh" >> "$mapping_file"
  echo "scripts/deploy-phases/phase1-staging.sh|scripts/core/phase1-staging.sh" >> "$mapping_file"
  echo "scripts/deploy-phases/phase2-prod-initial.sh|scripts/core/phase2-prod-initial.sh" >> "$mapping_file"
  echo "scripts/deploy-phases/phase3-prod-full.sh|scripts/core/phase3-prod-full.sh" >> "$mapping_file"
  
  # Testing scripts
  echo "scripts/smoke-test.js|scripts/testing/smoke-test.js" >> "$mapping_file"
  echo "scripts/enhanced-smoke-test.js|scripts/testing/enhanced-smoke-test.js" >> "$mapping_file"
  echo "scripts/e2e-staging-test.js|scripts/testing/e2e-staging-test.js" >> "$mapping_file"
  echo "scripts/run_tests.sh|scripts/testing/run_tests.sh" >> "$mapping_file"
  echo "scripts/run-chaos-tests.sh|scripts/testing/run-chaos-tests.sh" >> "$mapping_file"
  echo "scripts/test-ai-ml.sh|scripts/testing/test-ai-ml.sh" >> "$mapping_file"
  echo "scripts/load-testing.sh|scripts/testing/load-testing/load-testing.sh" >> "$mapping_file"
  echo "scripts/load_test.py|scripts/testing/load-testing/load_test.py" >> "$mapping_file"
  
  # Security scripts
  echo "scripts/automated-security-scan.sh|scripts/security/automated-security-scan.sh" >> "$mapping_file"
  echo "scripts/security-scanning.sh|scripts/security/security-scanning.sh" >> "$mapping_file"
  echo "scripts/secret-rotation.sh|scripts/security/secret-rotation.sh" >> "$mapping_file"
  echo "scripts/create-k8s-secrets.sh|scripts/security/create-k8s-secrets.sh" >> "$mapping_file"
  echo "scripts/setup-auth-security.sh|scripts/security/setup-auth-security.sh" >> "$mapping_file"
  
  # Infrastructure scripts
  echo "scripts/deploy-eks-cluster.sh|scripts/infrastructure/deploy-eks-cluster.sh" >> "$mapping_file"
  echo "scripts/setup-production-rds.sh|scripts/infrastructure/setup-production-rds.sh" >> "$mapping_file"
  echo "scripts/setup-redis-cluster.sh|scripts/infrastructure/setup-redis-cluster.sh" >> "$mapping_file"
  echo "scripts/deploy-cloudflare-waf.sh|scripts/infrastructure/deploy-cloudflare-waf.sh" >> "$mapping_file"
  echo "scripts/setup-devops-infrastructure.sh|scripts/infrastructure/setup-devops-infrastructure.sh" >> "$mapping_file"
  echo "scripts/setup-production-environment.sh|scripts/infrastructure/setup-production-environment.sh" >> "$mapping_file"
  echo "scripts/setup-datadog-monitoring.sh|scripts/infrastructure/setup-datadog-monitoring.sh" >> "$mapping_file"
  echo "scripts/configure-dns.sh|scripts/infrastructure/configure-dns.sh" >> "$mapping_file"
  echo "scripts/configure-ssl-tls.sh|scripts/infrastructure/configure-ssl-tls.sh" >> "$mapping_file"
  echo "scripts/automated-certificate-management.sh|scripts/infrastructure/automated-certificate-management.sh" >> "$mapping_file"
  
  # Database scripts
  echo "scripts/db-migration.sh|scripts/database/db-migration.sh" >> "$mapping_file"
  echo "scripts/check-migrations.sh|scripts/database/check-migrations.sh" >> "$mapping_file"
  echo "scripts/validate-migrations.js|scripts/database/validate-migrations.js" >> "$mapping_file"
  echo "scripts/schema-snapshot.sh|scripts/database/schema-snapshot.sh" >> "$mapping_file"
  echo "scripts/create-migration.sh|scripts/database/create-migration.sh" >> "$mapping_file"
  echo "scripts/configure-database-backups.sh|scripts/database/configure-database-backups.sh" >> "$mapping_file"
  echo "scripts/consolidate-migrations.sh|scripts/database/consolidate-migrations.sh" >> "$mapping_file"
  
  # Doc scripts
  echo "scripts/docs-automation.js|scripts/docs/docs-automation.js" >> "$mapping_file"
  echo "scripts/generate-api-docs.js|scripts/docs/generate-api-docs.js" >> "$mapping_file"
  echo "scripts/generate-inline-docs.js|scripts/docs/generate-inline-docs.js" >> "$mapping_file"
  echo "scripts/verify-doc-links.js|scripts/docs/verify-doc-links.js" >> "$mapping_file"
  echo "scripts/cleanup-docs.js|scripts/docs/cleanup-docs.js" >> "$mapping_file"
  echo "scripts/adr.js|scripts/docs/adr.js" >> "$mapping_file"
  echo "scripts/adr-template.md|scripts/docs/adr-template.md" >> "$mapping_file"
  
  # Utility scripts
  echo "scripts/check-dependencies.js|scripts/utils/check-dependencies.js" >> "$mapping_file"
  echo "scripts/check-critical-metrics.sh|scripts/utils/check-critical-metrics.sh" >> "$mapping_file"
  echo "scripts/automated-rollback.sh|scripts/utils/automated-rollback.sh" >> "$mapping_file"
  echo "scripts/generate-encryption-key.js|scripts/utils/generate-encryption-key.js" >> "$mapping_file"
  echo "scripts/generate-icons.js|scripts/utils/generate-icons.js" >> "$mapping_file"
  echo "scripts/update-dependencies.sh|scripts/utils/update-dependencies.sh" >> "$mapping_file"
  echo "scripts/update-missing-dependencies.js|scripts/utils/update-missing-dependencies.js" >> "$mapping_file"
  echo "scripts/docker-compose-env.sh|scripts/utils/docker-compose-env.sh" >> "$mapping_file"
  echo "scripts/source-env.sh|scripts/utils/source-env.sh" >> "$mapping_file"
  echo "scripts/get-refresh-token.js|scripts/utils/get-refresh-token.js" >> "$mapping_file"
  echo "scripts/setup-dev-environment.sh|scripts/utils/setup-dev-environment.sh" >> "$mapping_file"
  echo "scripts/install-core-deps.js|scripts/utils/install-core-deps.js" >> "$mapping_file"
  echo "scripts/install-shadcn.sh|scripts/utils/install-shadcn.sh" >> "$mapping_file"
  echo "scripts/verify-all-scripts.sh|scripts/utils/verify-all-scripts.sh" >> "$mapping_file"
  
  # Consolidated scripts
  echo "scripts/security-scanning.sh|scripts/security/security-scan.sh" >> "$mapping_file"
  echo "scripts/automated-security-scan.sh|scripts/security/security-scan.sh" >> "$mapping_file"
  echo "scripts/load-testing.sh|scripts/testing/load-testing/consolidated-load-test.sh" >> "$mapping_file"
  echo "scripts/load_test.py|scripts/testing/load-testing/consolidated-load-test.sh" >> "$mapping_file"
  echo "scripts/db-migration.sh|scripts/database/manage-migrations.sh" >> "$mapping_file"
  echo "scripts/check-migrations.sh|scripts/database/manage-migrations.sh" >> "$mapping_file"
  echo "scripts/schema-snapshot.sh|scripts/database/manage-migrations.sh" >> "$mapping_file"
  echo "scripts/create-migration.sh|scripts/database/manage-migrations.sh" >> "$mapping_file"
}

# Update references in a file
update_file() {
  local file="$1"
  local mapping_file="$2"
  local modified=false
  local temp_file=$(mktemp)
  
  log "Checking references in ${file}..."
  
  # Get list of old and new paths
  while IFS="|" read -r old_path new_path
  do
    # Check if the file contains the old path
    if grep -q "${old_path}" "${file}"; then
      modified=true
      
      if [ "${MODE}" = "auto" ]; then
        # Replace old path with new path
        sed "s|${old_path}|${new_path}|g" "${file}" > "${temp_file}"
        mv "${temp_file}" "${file}"
        log "  Updated: ${old_path} -> ${new_path}"
      else
        # Just report the change needed
        echo "  ${YELLOW}Found${NC}: ${old_path} -> ${new_path}"
      fi
    fi
  done < "${mapping_file}"
  
  # Clean up
  if [ -f "${temp_file}" ]; then
    rm -f "${temp_file}"
  fi
  
  if [ "${modified}" = true ]; then
    if [ "${MODE}" = "auto" ]; then
      log "File updated: ${file}"
    else
      echo "${YELLOW}File contains script references that need updating: ${file}${NC}"
    fi
    return 0
  else
    return 1
  fi
}

# Update references in all files
update_references() {
  local mapping_file=$(mktemp)
  generate_mapping_file "${mapping_file}"
  
  local updated_count=0
  
  # Find files with script references
  for file in $(find_script_references); do
    if update_file "${file}" "${mapping_file}"; then
      updated_count=$((updated_count + 1))
    fi
  done
  
  # Clean up
  rm -f "${mapping_file}"
  
  if [ "${updated_count}" -gt 0 ]; then
    if [ "${MODE}" = "auto" ]; then
      log "Updated references in ${updated_count} files"
    else
      log "Found references in ${updated_count} files that need updating"
    fi
  else
    log "No references needed updating"
  fi
}

# Print usage information
usage() {
  cat << EOF
Script Reference Updater (Simple version)

This script updates references to relocated scripts in CI/CD pipelines and other configuration files.

Usage: $(basename "$0") [options]

Options:
  --mode MODE     Mode of operation: 'auto' for automatic updates, 'report' for reporting only (default: report)
  --target DIR    Directory to scan for references (default: current directory)
  --help          Show this help message

Examples:
  $(basename "$0") --mode auto
  $(basename "$0") --target ./infrastructure
  $(basename "$0") --mode report --target ./kubernetes
EOF
}

# Parse command line arguments
while [ $# -gt 0 ]; do
  case $1 in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --target)
      TARGET="$2"
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

# Validate mode
if [ "${MODE}" != "auto" ] && [ "${MODE}" != "report" ]; then
  error "Invalid mode: ${MODE}"
  usage
  exit 1
fi

# Main function
main() {
  print_header
  update_references
  
  if [ "${MODE}" = "report" ]; then
    echo ""
    echo "${YELLOW}This was a dry run. To automatically update references, run:${NC}"
    echo "  $0 --mode auto"
  fi
  
  log "Script reference update completed"
}

# Run main function
main
