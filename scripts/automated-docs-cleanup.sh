#!/bin/bash

# Automated Documentation Cleanup Script
#
# This script automates the documentation cleanup process by running the cleanup
# script and committing the changes to the repository. It's designed to be run
# as part of a CI/CD pipeline or a scheduled cron job.

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCS_DIR="${REPO_ROOT}/docs"
CLEANUP_SCRIPT="${SCRIPT_DIR}/manual-cleanup-docs.js" # keeping original filename for compatibility
BRANCH_NAME="auto-docs-cleanup-$(date +%Y%m%d-%H%M%S)"
COMMIT_MESSAGE="Auto docs cleanup - $(date +%Y-%m-%d)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging function
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Check if running in CI environment
in_ci() {
  [ -n "${CI}" ] || [ -n "${GITHUB_ACTIONS}" ] || [ -n "${GITLAB_CI}" ] || [ -n "${JENKINS_URL}" ]
}

# Create a new branch if not in CI
create_branch() {
  if ! in_ci; then
    log "Creating branch ${BRANCH_NAME}..."
    git checkout -b "${BRANCH_NAME}"
  else
    log "Running in CI environment, skipping branch creation"
  fi
}

# Run cleanup script
run_cleanup() {
  log "Running documentation cleanup script..."
  node "${CLEANUP_SCRIPT}"

  if [ $? -ne 0 ]; then
    error "Documentation cleanup failed"
    exit 1
  fi
}

# Check if there are changes to commit
has_changes() {
  git status --porcelain | grep -q .
}

# Commit changes if any
commit_changes() {
  if has_changes; then
    log "Changes detected, committing..."
    git add "${DOCS_DIR}"
    git commit -m "${COMMIT_MESSAGE}"

    if ! in_ci; then
      log "Changes committed to branch ${BRANCH_NAME}"
      log "You can now review and push the changes:"
      log "  git push origin ${BRANCH_NAME}"
      log "Then create a pull request to merge these changes."
    else
      log "Changes committed in CI environment"
    fi
  else
    log "No changes to commit"
  fi
}

# Main function
main() {
  log "Starting automated documentation cleanup process..."

  # Navigate to repository root
  cd "${REPO_ROOT}"

  # Create branch if needed
  create_branch

  # Run cleanup script
  run_cleanup

  # Commit changes
  commit_changes

  log "Documentation cleanup process completed successfully"
}

# Run main function
main
