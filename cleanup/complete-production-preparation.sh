#!/bin/bash
set -e

# Complete Production Preparation Script for Maily
# This script runs all the required steps to prepare the repository for production

# Text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

# Directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Root directory of the project (parent of script dir)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}${BOLD}==================================================${RESET}"
echo -e "${BLUE}${BOLD}      MAILY PRODUCTION PREPARATION TOOLCHAIN      ${RESET}"
echo -e "${BLUE}${BOLD}==================================================${RESET}"
echo ""

# Function to check if a script exists and is executable
check_script() {
  local script="$1"
  if [ ! -f "$script" ]; then
    echo -e "${RED}Error: Script not found: $script${RESET}"
    exit 1
  fi

  if [ ! -x "$script" ]; then
    echo -e "${YELLOW}Making script executable: $script${RESET}"
    chmod +x "$script"
  fi
}

# Step 1: Run the main production cleanup
echo -e "${BLUE}${BOLD}STEP 1: Running primary production cleanup${RESET}"
echo -e "${BLUE}------------------------------------------${RESET}"
CLEANUP_SCRIPT="${SCRIPT_DIR}/production-cleanup.sh"
check_script "$CLEANUP_SCRIPT"
"$CLEANUP_SCRIPT"
echo -e "${GREEN}Production cleanup completed.${RESET}"
echo ""

# Step 2: Archive and remove backup directories
echo -e "${BLUE}${BOLD}STEP 2: Archive and remove backup directories${RESET}"
echo -e "${BLUE}------------------------------------------${RESET}"
ARCHIVE_SCRIPT="${SCRIPT_DIR}/archive-and-remove-backups.sh"
check_script "$ARCHIVE_SCRIPT"
"$ARCHIVE_SCRIPT"
echo -e "${GREEN}Backup management completed.${RESET}"
echo ""

# Step 3: Update .gitignore with enhanced patterns
echo -e "${BLUE}${BOLD}STEP 3: Update .gitignore with enhanced patterns${RESET}"
echo -e "${BLUE}------------------------------------------${RESET}"
GITIGNORE_SCRIPT="${SCRIPT_DIR}/update-gitignore.sh"
check_script "$GITIGNORE_SCRIPT"
"$GITIGNORE_SCRIPT"
echo -e "${GREEN}Gitignore enhancement completed.${RESET}"
echo ""

# Final summary
echo -e "${GREEN}${BOLD}==================================================${RESET}"
echo -e "${GREEN}${BOLD}      PRODUCTION PREPARATION COMPLETE!            ${RESET}"
echo -e "${GREEN}${BOLD}==================================================${RESET}"
echo ""

# Calculate final repository size
FINAL_SIZE=$(du -sh "${ROOT_DIR}" | cut -f1)
echo -e "Final repository size: ${BOLD}${FINAL_SIZE}${RESET}"
echo -e "The repository is now optimized for production deployment."
echo ""
echo -e "${BLUE}For more information about the cleanup process and recommendations:${RESET}"
echo -e "1. Cleanup strategy: ${YELLOW}PRODUCTION_CLEANUP_STRATEGY.md${RESET} (if available)"
echo -e "2. Cleanup results: ${YELLOW}PRODUCTION_CLEANUP_RESULTS.md${RESET}"
echo -e "3. Detailed cleanup report: ${YELLOW}cleanup/cleanup-report.md${RESET}"
echo ""
echo -e "${GREEN}${BOLD}Production preparation successfully completed!${RESET}"
