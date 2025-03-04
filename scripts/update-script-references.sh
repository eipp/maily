#!/usr/bin/env bash
# Script to update references to relocated scripts in CI/CD pipelines and other configuration files
# This script will scan specified files and directories for references to the old script paths
# and suggest or automatically update them to point to the new locations

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script path mappings
declare -A PATH_MAPPINGS
# Core deployment scripts
PATH_MAPPINGS["scripts/maily-deploy.sh"]="scripts/core/maily-deploy.sh"
PATH_MAPPINGS["scripts/deployment-validator.sh"]="scripts/core/deployment-validator.sh"
PATH_MAPPINGS["scripts/config-collector.sh"]="scripts/core/config-collector.sh"
PATH_MAPPINGS["scripts/update-image-tags.sh"]="scripts/core/update-image-tags.sh"
PATH_MAPPINGS["scripts/deploy-phases/phase1-staging.sh"]="scripts/core/phase1-staging.sh"
PATH_MAPPINGS["scripts/deploy-phases/phase2-prod-initial.sh"]="scripts/core/phase2-prod-initial.sh"
PATH_MAPPINGS["scripts/deploy-phases/phase3-prod-full.sh"]="scripts/core/phase3-prod-full.sh"

# Testing scripts
PATH_MAPPINGS["scripts/smoke-test.js"]="scripts/testing/smoke-test.js"
PATH_MAPPINGS["scripts/enhanced-smoke-test.js"]="scripts/testing/enhanced-smoke-test.js"
PATH_MAPPINGS["scripts/e2e-staging-test.js"]="scripts/testing/e2e-staging-test.js"
PATH_MAPPINGS["scripts/run_tests.sh"]="scripts/testing/run_tests.sh"
PATH_MAPPINGS["scripts/run-chaos-tests.sh"]="scripts/testing/run-chaos-tests.sh"
PATH_MAPPINGS["scripts/test-ai-ml.sh"]="scripts/testing/test-ai-ml.sh"
PATH_MAPPINGS["scripts/load-testing.sh"]="scripts/testing/load-testing/load-testing.sh"
PATH_MAPPINGS["scripts/load_test.py"]="scripts/testing/load-testing/load_test.py"

# Security scripts
PATH_MAPPINGS["scripts/automated-security-scan.sh"]="scripts/security/automated-security-scan.sh"
PATH_MAPPINGS["scripts/security-scanning.sh"]="scripts/security/security-scanning.sh"
PATH_MAPPINGS["scripts/secret-rotation.sh"]="scripts/security/secret-rotation.sh"
PATH_MAPPINGS["scripts/create-k8s-secrets.sh"]="scripts/security/create-k8s-secrets.sh"
PATH_MAPPINGS["scripts/setup-auth-security.sh"]="scripts/security/setup-auth-security.sh"

# Infrastructure scripts
PATH_MAPPINGS["scripts/deploy-eks-cluster.sh"]="scripts/infrastructure/deploy-eks-cluster.sh"
PATH_MAPPINGS["scripts/setup-production-rds.sh"]="scripts/infrastructure/setup-production-rds.sh"
PATH_MAPPINGS["scripts/setup-redis-cluster.sh"]="scripts/infrastructure/setup-redis-cluster.sh"
PATH_MAPPINGS["scripts/deploy-cloudflare-waf.sh"]="scripts/infrastructure/deploy-cloudflare-waf.sh"
PATH_MAPPINGS["scripts/setup-devops-infrastructure.sh"]="scripts/infrastructure/setup-devops-infrastructure.sh"
PATH_MAPPINGS["scripts/setup-production-environment.sh"]="scripts/infrastructure/setup-production-environment.sh"
PATH_MAPPINGS["scripts/setup-datadog-monitoring.sh"]="scripts/infrastructure/setup-datadog-monitoring.sh"
PATH_MAPPINGS["scripts/configure-dns.sh"]="scripts/infrastructure/configure-dns.sh"
PATH_MAPPINGS["scripts/configure-ssl-tls.sh"]="scripts/infrastructure/configure-ssl-tls.sh"
PATH_MAPPINGS["scripts/automated-certificate-management.sh"]="scripts/infrastructure/automated-certificate-management.sh"

# Database scripts
PATH_MAPPINGS["scripts/db-migration.sh"]="scripts/database/db-migration.sh"
PATH_MAPPINGS["scripts/check-migrations.sh"]="scripts/database/check-migrations.sh"
PATH_MAPPINGS["scripts/validate-migrations.js"]="scripts/database/validate-migrations.js"
PATH_MAPPINGS["scripts/schema-snapshot.sh"]="scripts/database/schema-snapshot.sh"
PATH_MAPPINGS["scripts/create-migration.sh"]="scripts/database/create-migration.sh"
PATH_MAPPINGS["scripts/configure-database-backups.sh"]="scripts/database/configure-database-backups.sh"
PATH_MAPPINGS["scripts/consolidate-migrations.sh"]="scripts/database/consolidate-migrations.sh"

# Doc scripts
PATH_MAPPINGS["scripts/docs-automation.js"]="scripts/docs/docs-automation.js"
PATH_MAPPINGS["scripts/generate-api-docs.js"]="scripts/docs/generate-api-docs.js"
PATH_MAPPINGS["scripts/generate-inline-docs.js"]="scripts/docs/generate-inline-docs.js"
PATH_MAPPINGS["scripts/verify-doc-links.js"]="scripts/docs/verify-doc-links.js"
PATH_MAPPINGS["scripts/cleanup-docs.js"]="scripts/docs/cleanup-docs.js"
PATH_MAPPINGS["scripts/adr.js"]="scripts/docs/adr.js"
PATH_MAPPINGS["scripts/adr-template.md"]="scripts/docs/adr-template.md"

# Utility scripts
PATH_MAPPINGS["scripts/check-dependencies.js"]="scripts/utils/check-dependencies.js"
PATH_MAPPINGS["scripts/check-critical-metrics.sh"]="scripts/utils/check-critical-metrics.sh"
PATH_MAPPINGS["scripts/automated-rollback.sh"]="scripts/utils/automated-rollback.sh"
PATH_MAPPINGS["scripts/generate-encryption-key.js"]="scripts/utils/generate-encryption-key.js"
PATH_MAPPINGS["scripts/generate-icons.js"]="scripts/utils/generate-icons.js"
PATH_MAPPINGS["scripts/update-dependencies.sh"]="scripts/utils/update-dependencies.sh"
PATH_MAPPINGS["scripts/update-missing-dependencies.js"]="scripts/utils/update-missing-dependencies.js"
PATH_MAPPINGS["scripts/docker-compose-env.sh"]="scripts/utils/docker-compose-env.sh"
PATH_MAPPINGS["scripts/source-env.sh"]="scripts/utils/source-env.sh"
PATH_MAPPINGS["scripts/get-refresh-token.js"]="scripts/utils/get-refresh-token.js"
PATH_MAPPINGS["scripts/setup-dev-environment.sh"]="scripts/utils/setup-dev-environment.sh"
PATH_MAPPINGS["scripts/install-core-deps.js"]="scripts/utils/install-core-deps.js"
PATH_MAPPINGS["scripts/install-shadcn.sh"]="scripts/utils/install-shadcn.sh"
PATH_MAPPINGS["scripts/verify-all-scripts.sh"]="scripts/utils/verify-all-scripts.sh"

# Consolidated scripts
PATH_MAPPINGS["scripts/security-scanning.sh"]="scripts/security/security-scan.sh"
PATH_MAPPINGS["scripts/automated-security-scan.sh"]="scripts/security/security-scan.sh"
PATH_MAPPINGS["scripts/load-testing.sh"]="scripts/testing/load-testing/consolidated-load-test.sh"
PATH_MAPPINGS["scripts/load_test.py"]="scripts/testing/load-testing/consolidated-load-test.sh"
PATH_MAPPINGS["scripts/db-migration.sh"]="scripts/database/manage-migrations.sh"
PATH_MAPPINGS["scripts/check-migrations.sh"]="scripts/database/manage-migrations.sh"
PATH_MAPPINGS["scripts/schema-snapshot.sh"]="scripts/database/manage-migrations.sh"
PATH_MAPPINGS["scripts/create-migration.sh"]="scripts/database/manage-migrations.sh"

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

# Print header
print_header() {
  echo -e "${BLUE}=================================================="
  echo -e "          SCRIPT REFERENCE UPDATER           "
  echo -e "==================================================${NC}"
  echo ""
  echo -e "Mode: ${MODE}"
  echo -e "Target: ${TARGET}"
  echo ""
}

# Find references to old script paths in files
find_references() {
  local target="$1"
  
  log "Scanning files in ${target} for script references..."
  
  # Find all text files, excluding binary files, .git, node_modules, and other irrelevant directories
  find "${target}" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" -not -path "*/build/*" \
    -not -name "*.png" -not -name "*.jpg" -not -name "*.jpeg" -not -name "*.gif" -not -name "*.ico" \
    -not -name "*.woff" -not -name "*.woff2" -not -name "*.ttf" -not -name "*.eot" -not -name "*.svg" \
    -not -name "*.pdf" -not -name "*.exe" -not -name "*.dll" -not -name "*.so" -not -name "*.dylib" \
    -print0 | xargs -0 grep -l "scripts/" 2>/dev/null || true
}

# Update references in a file
update_file() {
  local file="$1"
  local modified=false
  local temp_file=$(mktemp)
  
  log "Updating references in ${file}..."
  
  # Check and update each path mapping
  for old_path in "${!PATH_MAPPINGS[@]}"; do
    local new_path="${PATH_MAPPINGS[$old_path]}"
    
    # Check if the file contains the old path
    if grep -q "${old_path}" "${file}"; then
      modified=true
      
      if [ "${MODE}" = "auto" ]; then
        # Replace old path with new path
        sed "s|${old_path}|${new_path}|g" "${file}" > "${temp_file}"
        cp "${temp_file}" "${file}"
        log "  Updated: ${old_path} -> ${new_path}"
      else
        # Just report the change needed
        echo -e "  ${YELLOW}Found${NC}: ${old_path} -> ${new_path}"
      fi
    fi
  done
  
  rm "${temp_file}"
  
  if [ "${modified}" = true ]; then
    if [ "${MODE}" = "auto" ]; then
      log "File updated: ${file}"
    else
      echo -e "${YELLOW}File contains script references that need updating: ${file}${NC}"
    fi
    return 0
  else
    return 1
  fi
}

# Update references in all files
update_references() {
  local target="$1"
  local updated_count=0
  local file_list=$(find_references "${target}")
  
  # Check if any files were found
  if [ -z "${file_list}" ]; then
    log "No files found with script references in ${target}"
    return 0
  fi
  
  for file in ${file_list}; do
    if update_file "${file}"; then
      updated_count=$((updated_count + 1))
    fi
  done
  
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
Script Reference Updater

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
MODE="report"
TARGET="."

while [[ $# -gt 0 ]]; do
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
  update_references "${TARGET}"
  
  if [ "${MODE}" = "report" ]; then
    echo ""
    echo -e "${YELLOW}This was a dry run. To automatically update references, run:${NC}"
    echo "  $0 --mode auto"
  fi
  
  log "Script reference update completed"
}

# Run main function
main
