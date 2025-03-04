#!/bin/sh
# Simple script to find and update script references in files
# This script finds all files that contain script references and updates them

# Configuration
MODE="report"
TARGET="."

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
      echo "Usage: $0 [--mode auto|report] [--target directory]"
      echo ""
      echo "Options:"
      echo "  --mode MODE     Mode of operation: 'auto' for automatic updates, 'report' for reporting only (default: report)"
      echo "  --target DIR    Directory to scan for references (default: current directory)"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Print header
echo "SCRIPT REFERENCE UPDATER"
echo "========================="
echo ""
echo "Mode: ${MODE}"
echo "Target: ${TARGET}"
echo ""

# Create mapping file
create_mapping_file() {
  echo "scripts/maily-deploy.sh|scripts/core/maily-deploy.sh" > "$1"
  echo "scripts/deployment-validator.sh|scripts/core/deployment-validator.sh" >> "$1"
  echo "scripts/config-collector.sh|scripts/core/config-collector.sh" >> "$1"
  echo "scripts/update-image-tags.sh|scripts/core/update-image-tags.sh" >> "$1"
  echo "scripts/deploy-phases/phase1-staging.sh|scripts/core/phase1-staging.sh" >> "$1"
  echo "scripts/deploy-phases/phase2-prod-initial.sh|scripts/core/phase2-prod-initial.sh" >> "$1"
  echo "scripts/deploy-phases/phase3-prod-full.sh|scripts/core/phase3-prod-full.sh" >> "$1"
  echo "scripts/smoke-test.js|scripts/testing/smoke-test.js" >> "$1"
  echo "scripts/enhanced-smoke-test.js|scripts/testing/enhanced-smoke-test.js" >> "$1"
  echo "scripts/e2e-staging-test.js|scripts/testing/e2e-staging-test.js" >> "$1"
  echo "scripts/run_tests.sh|scripts/testing/run_tests.sh" >> "$1"
  echo "scripts/run-chaos-tests.sh|scripts/testing/run-chaos-tests.sh" >> "$1"
  echo "scripts/test-ai-ml.sh|scripts/testing/test-ai-ml.sh" >> "$1"
  echo "scripts/load-testing.sh|scripts/testing/load-testing/load-testing.sh" >> "$1"
  echo "scripts/load_test.py|scripts/testing/load-testing/load_test.py" >> "$1"
  echo "scripts/automated-security-scan.sh|scripts/security/automated-security-scan.sh" >> "$1"
  echo "scripts/security-scanning.sh|scripts/security/security-scanning.sh" >> "$1"
  echo "scripts/secret-rotation.sh|scripts/security/secret-rotation.sh" >> "$1"
  echo "scripts/create-k8s-secrets.sh|scripts/security/create-k8s-secrets.sh" >> "$1"
  echo "scripts/setup-auth-security.sh|scripts/security/setup-auth-security.sh" >> "$1"
  echo "scripts/deploy-eks-cluster.sh|scripts/infrastructure/deploy-eks-cluster.sh" >> "$1"
  echo "scripts/setup-production-rds.sh|scripts/infrastructure/setup-production-rds.sh" >> "$1"
  echo "scripts/setup-redis-cluster.sh|scripts/infrastructure/setup-redis-cluster.sh" >> "$1"
  echo "scripts/deploy-cloudflare-waf.sh|scripts/infrastructure/deploy-cloudflare-waf.sh" >> "$1"
  echo "scripts/setup-devops-infrastructure.sh|scripts/infrastructure/setup-devops-infrastructure.sh" >> "$1"
  echo "scripts/setup-production-environment.sh|scripts/infrastructure/setup-production-environment.sh" >> "$1"
  echo "scripts/setup-datadog-monitoring.sh|scripts/infrastructure/setup-datadog-monitoring.sh" >> "$1"
  echo "scripts/configure-dns.sh|scripts/infrastructure/configure-dns.sh" >> "$1"
  echo "scripts/configure-ssl-tls.sh|scripts/infrastructure/configure-ssl-tls.sh" >> "$1"
  echo "scripts/automated-certificate-management.sh|scripts/infrastructure/automated-certificate-management.sh" >> "$1"
  echo "scripts/db-migration.sh|scripts/database/db-migration.sh" >> "$1"
  echo "scripts/check-migrations.sh|scripts/database/check-migrations.sh" >> "$1"
  echo "scripts/validate-migrations.js|scripts/database/validate-migrations.js" >> "$1"
  echo "scripts/schema-snapshot.sh|scripts/database/schema-snapshot.sh" >> "$1"
  echo "scripts/create-migration.sh|scripts/database/create-migration.sh" >> "$1"
  echo "scripts/configure-database-backups.sh|scripts/database/configure-database-backups.sh" >> "$1"
  echo "scripts/consolidate-migrations.sh|scripts/database/consolidate-migrations.sh" >> "$1"
  echo "scripts/docs-automation.js|scripts/docs/docs-automation.js" >> "$1"
  echo "scripts/generate-api-docs.js|scripts/docs/generate-api-docs.js" >> "$1"
  echo "scripts/generate-inline-docs.js|scripts/docs/generate-inline-docs.js" >> "$1"
  echo "scripts/verify-doc-links.js|scripts/docs/verify-doc-links.js" >> "$1"
  echo "scripts/cleanup-docs.js|scripts/docs/cleanup-docs.js" >> "$1"
  echo "scripts/adr.js|scripts/docs/adr.js" >> "$1"
  echo "scripts/adr-template.md|scripts/docs/adr-template.md" >> "$1"
  echo "scripts/check-dependencies.js|scripts/utils/check-dependencies.js" >> "$1"
  echo "scripts/check-critical-metrics.sh|scripts/utils/check-critical-metrics.sh" >> "$1"
  echo "scripts/automated-rollback.sh|scripts/utils/automated-rollback.sh" >> "$1"
  echo "scripts/generate-encryption-key.js|scripts/utils/generate-encryption-key.js" >> "$1"
  echo "scripts/generate-icons.js|scripts/utils/generate-icons.js" >> "$1"
  echo "scripts/update-dependencies.sh|scripts/utils/update-dependencies.sh" >> "$1"
  echo "scripts/update-missing-dependencies.js|scripts/utils/update-missing-dependencies.js" >> "$1"
  echo "scripts/docker-compose-env.sh|scripts/utils/docker-compose-env.sh" >> "$1"
  echo "scripts/source-env.sh|scripts/utils/source-env.sh" >> "$1"
  echo "scripts/get-refresh-token.js|scripts/utils/get-refresh-token.js" >> "$1"
  echo "scripts/setup-dev-environment.sh|scripts/utils/setup-dev-environment.sh" >> "$1"
  echo "scripts/install-core-deps.js|scripts/utils/install-core-deps.js" >> "$1"
  echo "scripts/install-shadcn.sh|scripts/utils/install-shadcn.sh" >> "$1"
  echo "scripts/verify-all-scripts.sh|scripts/utils/verify-all-scripts.sh" >> "$1"
  # Consolidated scripts
  echo "scripts/security-scanning.sh|scripts/security/security-scan.sh" >> "$1"
  echo "scripts/automated-security-scan.sh|scripts/security/security-scan.sh" >> "$1"
  echo "scripts/load-testing.sh|scripts/testing/load-testing/consolidated-load-test.sh" >> "$1"
  echo "scripts/load_test.py|scripts/testing/load-testing/consolidated-load-test.sh" >> "$1"
  echo "scripts/db-migration.sh|scripts/database/manage-migrations.sh" >> "$1"
  echo "scripts/check-migrations.sh|scripts/database/manage-migrations.sh" >> "$1"
  echo "scripts/schema-snapshot.sh|scripts/database/manage-migrations.sh" >> "$1"
  echo "scripts/create-migration.sh|scripts/database/manage-migrations.sh" >> "$1"
}

# Main function
main() {
  echo "Scanning files in ${TARGET} for script references..."
  
  # Create temporary mapping file
  MAPPING_FILE=$(mktemp)
  create_mapping_file "${MAPPING_FILE}"
  
  # Find all text files
  FILES=$(find "${TARGET}" -type f \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/dist/*" \
    -not -path "*/build/*" \
    -not -name "*.png" \
    -not -name "*.jpg" \
    -not -name "*.jpeg" \
    -not -name "*.gif" \
    -not -name "*.ico" \
    -not -name "*.woff" \
    -not -name "*.woff2" \
    -not -name "*.ttf" \
    -not -name "*.eot" \
    -not -name "*.svg" \
    -not -name "*.pdf" \
    -not -name "*.exe" \
    -not -name "*.dll" \
    -not -name "*.so" \
    -not -name "*.dylib" 2>/dev/null)
  
  # Count of updated files
  UPDATED_COUNT=0
  
  # Process each file
  for FILE in $FILES; do
    # Check if file contains references to scripts/
    if grep -q "scripts/" "${FILE}" 2>/dev/null; then
      echo "Checking file: ${FILE}"
      
      # Create temporary file for modifications
      TEMP_FILE=$(mktemp)
      cp "${FILE}" "${TEMP_FILE}"
      
      # Flag to track if the file was modified
      MODIFIED=0
      
      # Process each mapping
      while IFS="|" read -r OLD_PATH NEW_PATH; do
        # Check if file contains the old path
        if grep -q "${OLD_PATH}" "${TEMP_FILE}" 2>/dev/null; then
          if [ "${MODE}" = "auto" ]; then
            # Replace the old path with the new path
            sed -i.bak "s|${OLD_PATH}|${NEW_PATH}|g" "${TEMP_FILE}" 2>/dev/null
            if [ $? -ne 0 ]; then
              # If sed -i fails (e.g., on macOS), try alternative approach
              sed "s|${OLD_PATH}|${NEW_PATH}|g" "${TEMP_FILE}" > "${TEMP_FILE}.new"
              mv "${TEMP_FILE}.new" "${TEMP_FILE}"
            fi
            rm -f "${TEMP_FILE}.bak" 2>/dev/null
            
            echo "  Updated: ${OLD_PATH} -> ${NEW_PATH}"
            MODIFIED=1
          else
            echo "  Would update: ${OLD_PATH} -> ${NEW_PATH}"
            MODIFIED=1
          fi
        fi
      done < "${MAPPING_FILE}"
      
      # If the file was modified and we're in auto mode, copy it back
      if [ "${MODIFIED}" -eq 1 ] && [ "${MODE}" = "auto" ]; then
        cp "${TEMP_FILE}" "${FILE}"
        UPDATED_COUNT=$((UPDATED_COUNT + 1))
      elif [ "${MODIFIED}" -eq 1 ]; then
        UPDATED_COUNT=$((UPDATED_COUNT + 1))
      fi
      
      # Clean up temporary file
      rm -f "${TEMP_FILE}"
    fi
  done
  
  # Clean up mapping file
  rm -f "${MAPPING_FILE}"
  
  # Summary
  echo ""
  if [ "${UPDATED_COUNT}" -gt 0 ]; then
    if [ "${MODE}" = "auto" ]; then
      echo "Updated references in ${UPDATED_COUNT} files"
    else
      echo "Found references in ${UPDATED_COUNT} files that need updating"
    fi
  else
    echo "No references needed updating"
  fi
  
  echo ""
  if [ "${MODE}" = "report" ]; then
    echo "This was a dry run. To automatically update references, run:"
    echo "$0 --mode auto"
  fi
}

# Run main function
