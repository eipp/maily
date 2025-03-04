#!/bin/sh
# Script to verify the success of the script consolidation
# This performs a series of checks to ensure all scripts were migrated properly

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Logging functions
log() {
  echo "${GREEN}[INFO] $1${NC}"
}

warn() {
  echo "${YELLOW}[WARN] $1${NC}"
}

error() {
  echo "${RED}[ERROR] $1${NC}"
}

# Print header
echo "${BLUE}====================================================="
echo "          SCRIPT CONSOLIDATION VERIFICATION           "
echo "=====================================================${NC}"
echo ""

# Check consolidated scripts
check_consolidated_scripts() {
  log "Checking consolidated scripts..."
  
  # Check security scan script
  if [ ! -f "scripts/security/security-scan.sh" ]; then
    error "Consolidated security scan script not found!"
  else
    log "✓ Security scan script exists"
    if [ ! -x "scripts/security/security-scan.sh" ]; then
      warn "Security scan script is not executable. Fix with: chmod +x scripts/security/security-scan.sh"
    else
      log "✓ Security scan script is executable"
    fi
  fi
  
  # Check load testing script
  if [ ! -f "scripts/testing/load-testing/consolidated-load-test.sh" ]; then
    error "Consolidated load testing script not found!"
  else
    log "✓ Load testing script exists"
    if [ ! -x "scripts/testing/load-testing/consolidated-load-test.sh" ]; then
      warn "Load testing script is not executable. Fix with: chmod +x scripts/testing/load-testing/consolidated-load-test.sh"
    else
      log "✓ Load testing script is executable"
    fi
  fi
  
  # Check database migration script
  if [ ! -f "scripts/database/manage-migrations.sh" ]; then
    error "Consolidated database migration script not found!"
  else
    log "✓ Database migration script exists"
    if [ ! -x "scripts/database/manage-migrations.sh" ]; then
      warn "Database migration script is not executable. Fix with: chmod +x scripts/database/manage-migrations.sh"
    else
      log "✓ Database migration script is executable"
    fi
  fi
  
  echo ""
}

# Check migration utilities
check_migration_utilities() {
  log "Checking migration utilities..."
  
  # Check update references script
  if [ ! -f "scripts/update-references.sh" ]; then
    error "Update references script not found!"
  else
    log "✓ Update references script exists"
    if [ ! -x "scripts/update-references.sh" ]; then
      warn "Update references script is not executable. Fix with: chmod +x scripts/update-references.sh"
    else
      log "✓ Update references script is executable"
    fi
  fi
  
  # Check cleanup script
  if [ ! -f "scripts/cleanup-redundant-scripts.sh" ]; then
    error "Cleanup redundant scripts script not found!"
  else
    log "✓ Cleanup redundant scripts script exists"
    if [ ! -x "scripts/cleanup-redundant-scripts.sh" ]; then
      warn "Cleanup redundant scripts script is not executable. Fix with: chmod +x scripts/cleanup-redundant-scripts.sh"
    else
      log "✓ Cleanup redundant scripts script is executable"
    fi
  fi
  
  echo ""
}

# Check documentation
check_documentation() {
  log "Checking documentation..."
  
  # Check consolidation plan
  if [ ! -f "scripts/CONSOLIDATION-PLAN.md" ]; then
    error "Consolidation plan document not found!"
  else
    log "✓ Consolidation plan document exists"
  fi
  
  # Check redundant scripts list
  if [ ! -f "scripts/REDUNDANT-SCRIPTS.md" ]; then
    error "Redundant scripts document not found!"
  else
    log "✓ Redundant scripts document exists"
  fi
  
  echo ""
}

# Check directory structure
check_directory_structure() {
  log "Checking directory structure..."
  
  for dir in "core" "testing" "security" "infrastructure" "database" "docs" "utils"; do
    if [ ! -d "scripts/$dir" ]; then
      error "Directory scripts/$dir not found!"
    else
      log "✓ Directory scripts/$dir exists"
      count=$(find "scripts/$dir" -type f | wc -l | tr -d ' ')
      log "  - Contains $count files"
    fi
  done
  
  echo ""
}

# Check if redundant scripts still exist
check_redundant_scripts() {
  log "Checking for redundant scripts..."
  
  # Check if cleanup has been run
  REDUNDANT_FOUND=0
  
  # Utility scripts that should not be considered redundant
  UTILITIES="scripts/update-references.sh scripts/cleanup-redundant-scripts.sh scripts/verify-consolidation.sh"
  
  # Read the list of redundant scripts
  while read -r line; do
    # Skip lines that don't start with "scripts/"
    if echo "$line" | grep -q "^scripts/"; then
      script=$(echo "$line" | grep -o "scripts/[^ ]*" | tr -d "|" | tr -d '`')
      
      # Skip utility scripts
      if echo "${UTILITIES}" | grep -q "${script}"; then
        continue
      fi
      
      if [ -f "$script" ]; then
        warn "Redundant script still exists: $script"
        REDUNDANT_FOUND=$((REDUNDANT_FOUND + 1))
      fi
    fi
  done < scripts/REDUNDANT-SCRIPTS.md
  
  if [ $REDUNDANT_FOUND -eq 0 ]; then
    log "✓ All redundant scripts have been removed"
  else
    warn "$REDUNDANT_FOUND redundant scripts still exist. Run cleanup script to remove them:"
    echo "  scripts/cleanup-redundant-scripts.sh --mode delete"
  fi
  
  echo ""
}

# Summary
summary() {
  log "Verification complete!"
  echo ""
  echo "${BLUE}Next steps:${NC}"
  echo "1. If any issues were found, fix them using the suggested commands"
  echo "2. Update script references:"
  echo "   scripts/update-references.sh --mode auto"
  echo "3. Test the consolidated scripts with sample workloads"
  echo "4. Remove redundant scripts if verification is successful:"
  echo "   scripts/cleanup-redundant-scripts.sh --mode delete"
  echo ""
}

# Run all checks
check_consolidated_scripts
check_migration_utilities
check_documentation
check_directory_structure
check_redundant_scripts
summary
