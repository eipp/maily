#!/bin/sh
# Script to safely remove redundant scripts after consolidation
# This script makes backups before deleting any files

# Colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Configuration
BACKUP_DIR="scripts/backup_before_cleanup_$(date +%Y%m%d%H%M%S)"
MODE="dry-run"  # Options: dry-run, backup-only, delete

# Redundant scripts to be removed
# Format: one script path per line
cat > /tmp/redundant_scripts.txt << EOF
scripts/load-testing.sh
scripts/load_test.py
scripts/automated-security-scan.sh
scripts/security-scanning.sh
scripts/db-migration.sh
scripts/check-migrations.sh
scripts/schema-snapshot.sh
scripts/create-migration.sh
scripts/validate-migrations.js
scripts/consolidate-migrations.sh
scripts/deploy-phases/phase1-staging.sh
scripts/deploy-phases/phase2-prod-initial.sh
scripts/deploy-phases/phase3-prod-full.sh
scripts/performance/test_blockchain_performance.js
scripts/performance/locustfile.py
scripts/performance/load_test.py
scripts/performance/test_canvas_performance.js
EOF

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
  echo "          SCRIPT CLEANUP UTILITY           "
  echo "==================================================${NC}"
  echo ""
  echo "Mode: ${MODE}"
  echo "Backup directory: ${BACKUP_DIR}"
  echo ""
}

# Parse command line arguments
while [ $# -gt 0 ]; do
  case $1 in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--mode dry-run|backup-only|delete] [--backup-dir directory]"
      echo ""
      echo "Options:"
      echo "  --mode MODE       Operation mode: dry-run (default), backup-only, or delete"
      echo "  --backup-dir DIR  Directory to store backups (default: scripts/backup_before_cleanup_<timestamp>)"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate mode
if [ "${MODE}" != "dry-run" ] && [ "${MODE}" != "backup-only" ] && [ "${MODE}" != "delete" ]; then
  error "Invalid mode: ${MODE}"
  echo "Valid modes: dry-run, backup-only, delete"
  exit 1
fi

# Create backup directory
create_backup_dir() {
  if [ -d "${BACKUP_DIR}" ]; then
    warn "Backup directory already exists: ${BACKUP_DIR}"
  else
    mkdir -p "${BACKUP_DIR}"
    log "Created backup directory: ${BACKUP_DIR}"
  fi
}

# Backup a file
backup_file() {
  local file="$1"
  
  if [ ! -f "${file}" ]; then
    warn "File not found, cannot backup: ${file}"
    return 1
  fi
  
  # Create parent directories in backup
  local parent_dir=$(dirname "${file}")
  mkdir -p "${BACKUP_DIR}/${parent_dir}"
  
  # Copy file to backup
  cp -p "${file}" "${BACKUP_DIR}/${file}"
  log "Backed up: ${file}"
}

# Delete a file
delete_file() {
  local file="$1"
  
  if [ ! -f "${file}" ]; then
    warn "File not found, cannot delete: ${file}"
    return 1
  fi
  
  rm "${file}"
  log "Deleted: ${file}"
}

# Main function
main() {
  print_header
  
  # Check if we need to create backup directory
  if [ "${MODE}" = "backup-only" ] || [ "${MODE}" = "delete" ]; then
    create_backup_dir
  fi
  
  # Process each redundant script
  log "Processing redundant scripts..."
  local count=0
  
  while read -r file; do
    if [ -z "${file}" ] || [ "${file}" = "#"* ]; then
      # Skip empty lines and comments
      continue
    fi
    
    if [ -f "${file}" ]; then
      case "${MODE}" in
        dry-run)
          log "Would remove: ${file}"
          count=$((count + 1))
          ;;
        backup-only)
          backup_file "${file}"
          count=$((count + 1))
          ;;
        delete)
          backup_file "${file}" && delete_file "${file}"
          count=$((count + 1))
          ;;
      esac
    else
      warn "File does not exist: ${file}"
    fi
  done < /tmp/redundant_scripts.txt
  
  # Clean up
  rm /tmp/redundant_scripts.txt
  
  # Summary
  log "Processed ${count} redundant scripts"
  
  case "${MODE}" in
    dry-run)
      echo ""
      echo "${YELLOW}This was a dry run. No files were modified.${NC}"
      echo "To backup the files, run: $0 --mode backup-only"
      echo "To backup and delete the files, run: $0 --mode delete"
      ;;
    backup-only)
      echo ""
      echo "${YELLOW}Files were backed up to: ${BACKUP_DIR}${NC}"
      echo "To delete the files, run: $0 --mode delete"
      ;;
    delete)
      echo ""
      echo "${GREEN}Files were backed up to ${BACKUP_DIR} and then deleted.${NC}"
      ;;
  esac
}

# Run main function
main
