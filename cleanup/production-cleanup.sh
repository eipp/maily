#!/bin/bash
set -e

# Production Cleanup Script for Maily
# This script safely removes unnecessary files and directories before production deployment

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

# Create backup of the repository before making changes
create_backup() {
  echo -e "${BLUE}${BOLD}Creating backup of the repository...${RESET}"
  BACKUP_DIR="${ROOT_DIR}/backups/pre_production_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$BACKUP_DIR"

  # Exclude node_modules, .git, and other large directories from the backup
  rsync -a --exclude="node_modules" --exclude=".venv" --exclude=".git" \
        --exclude="dist" --exclude="build" --exclude=".next" \
        --exclude="coverage_html" --exclude="metricbeat-*" \
        "${ROOT_DIR}/" "${BACKUP_DIR}/"

  echo -e "${GREEN}Backup created at ${BACKUP_DIR}${RESET}"
  echo "If anything goes wrong, you can restore from this backup."
}

# Function to get relative path (macOS compatible)
get_relative_path() {
  local path="$1"
  local base="$2"

  # Use parameter expansion to remove base path prefix
  echo "${path#$base/}"
}

# Log function for tracking removed files
log_removed() {
  local file="$1"
  local reason="$2"
  echo "$file,$reason,$(date +%Y-%m-%d\ %H:%M:%S)" >> "${SCRIPT_DIR}/cleanup-report.csv"
}

# Function to remove files/directories if they exist
remove_if_exists() {
  local path="$1"
  local reason="$2"
  local full_path="${ROOT_DIR}/${path}"

  if [ -e "$full_path" ]; then
    echo -e "${YELLOW}Removing: ${full_path}${RESET}"
    rm -rf "$full_path"
    log_removed "$path" "$reason"
  fi
}

# Initialize the cleanup report with headers
initialize_report() {
  echo "File/Directory,Reason,Timestamp" > "${SCRIPT_DIR}/cleanup-report.csv"
  echo "# Maily Production Cleanup Report" > "${SCRIPT_DIR}/cleanup-report.md"
  echo "Generated: $(date)" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "## Summary" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "" >> "${SCRIPT_DIR}/cleanup-report.md"
}

# Prompt before continuing with destructive operations
prompt_confirmation() {
  echo -e "${RED}${BOLD}WARNING: This script will permanently remove files from your repository.${RESET}"
  echo -e "A backup will be created, but please make sure you have committed all important changes."
  echo ""
  read -p "Continue with cleanup? (y/n): " confirm

  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Cleanup canceled."
    exit 0
  fi
}

# Track metrics for the cleanup report
initialize_metrics() {
  TOTAL_REMOVED=0
  TOTAL_SIZE_SAVED=0
  REPO_SIZE_BEFORE=$(du -sh "${ROOT_DIR}" | cut -f1)
}

# Update the cleanup metrics
update_metrics() {
  TOTAL_REMOVED=$((TOTAL_REMOVED + 1))
  # Add size calculation later
}

# Print final cleanup report
generate_report() {
  REPO_SIZE_AFTER=$(du -sh "${ROOT_DIR}" | cut -f1)

  echo -e "\n${GREEN}${BOLD}Cleanup Complete!${RESET}\n"
  echo -e "Repository size before: ${REPO_SIZE_BEFORE}"
  echo -e "Repository size after:  ${REPO_SIZE_AFTER}"
  echo -e "Total items removed: ${TOTAL_REMOVED}"

  # Update the markdown report
  echo "- **Repository size before:** ${REPO_SIZE_BEFORE}" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "- **Repository size after:** ${REPO_SIZE_AFTER}" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "- **Total items removed:** ${TOTAL_REMOVED}" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "## Removed Items" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "| File/Directory | Reason |" >> "${SCRIPT_DIR}/cleanup-report.md"
  echo "|---------------|--------|" >> "${SCRIPT_DIR}/cleanup-report.md"

  # Convert CSV to markdown table
  tail -n +2 "${SCRIPT_DIR}/cleanup-report.csv" | while IFS=, read -r file reason timestamp; do
    echo "| \`$file\` | $reason |" >> "${SCRIPT_DIR}/cleanup-report.md"
  done
}

# Safely remove files with find command
find_and_remove_files() {
  local pattern="$1"
  local reason="$2"
  local dir="${3:-$ROOT_DIR}"

  find "$dir" -name "$pattern" -type f 2>/dev/null | while read -r file; do
    # Get the relative path for reporting
    rel_path=$(get_relative_path "$file" "$ROOT_DIR")
    echo -e "${YELLOW}Removing: ${file}${RESET}"
    rm -f "$file"
    log_removed "$rel_path" "$reason"
    update_metrics
  done
}

main() {
  prompt_confirmation
  initialize_report
  initialize_metrics
  create_backup

  echo -e "\n${BLUE}${BOLD}Starting repository cleanup...${RESET}\n"

  # 1. Remove log files and directories
  echo -e "\n${BLUE}Removing log files...${RESET}"
  find_and_remove_files "*.log" "Log file"
  remove_if_exists "logs" "Log directory"

  # 2. Remove development environment files
  echo -e "\n${BLUE}Removing development environment files...${RESET}"
  remove_if_exists ".env" "Development environment file"
  remove_if_exists ".env.development" "Development environment file"
  remove_if_exists ".env.test" "Test environment file"
  remove_if_exists ".env.staging" "Staging environment file"
  # Note: We keep .env.production and .env.example

  # 3. Remove test files and directories
  echo -e "\n${BLUE}Removing test artifacts...${RESET}"
  remove_if_exists "coverage_html" "Test coverage reports"
  remove_if_exists "coverage.json" "Test coverage data"
  remove_if_exists "test_report_*.json" "Test report files"
  remove_if_exists "test_report_*.html" "Test report files"
  remove_if_exists "test_results.xml" "Test results file"

  # 4. Remove diagnostic and debug files
  echo -e "\n${BLUE}Removing diagnostic and debug files...${RESET}"
  remove_if_exists "diagnostic_reports" "Diagnostic reports directory"
  remove_if_exists "run_diagnostics.sh" "Diagnostic script"
  remove_if_exists "diagnostics" "Diagnostics directory"

  # 5. Remove development-only directories
  echo -e "\n${BLUE}Removing development-only directories...${RESET}"
  remove_if_exists "dev" "Development directory"
  remove_if_exists "performance" "Performance testing directory"
  remove_if_exists ".cursor" "Cursor IDE config directory"
  remove_if_exists ".zap" "ZAP scanner results"
  remove_if_exists ".venv" "Python virtual environment"
  remove_if_exists "node_modules" "Node.js dependencies (will be reinstalled in build process)"

  # 6. Remove build artifacts in apps
  echo -e "\n${BLUE}Removing build artifacts...${RESET}"
  find "${ROOT_DIR}" -path "*/apps/*/node_modules" -type d 2>/dev/null | while read -r dir; do
    rel_path=$(get_relative_path "$dir" "$ROOT_DIR")
    echo -e "${YELLOW}Removing: ${dir}${RESET}"
    rm -rf "$dir"
    log_removed "$rel_path" "Nested node_modules"
    update_metrics
  done

  find "${ROOT_DIR}" -path "*/.next" -type d 2>/dev/null | while read -r dir; do
    rel_path=$(get_relative_path "$dir" "$ROOT_DIR")
    echo -e "${YELLOW}Removing: ${dir}${RESET}"
    rm -rf "$dir"
    log_removed "$rel_path" "Next.js build artifacts"
    update_metrics
  done

  find_and_remove_files "*.tsbuildinfo" "TypeScript build info"

  # 7. Remove large binary files
  echo -e "\n${BLUE}Removing large binary files...${RESET}"
  remove_if_exists "metricbeat-8.12.0-darwin-x86_64.tar.gz" "Large binary archive"
  remove_if_exists "metricbeat-8.12.0-darwin-x86_64" "Extracted binary package"

  # 8. Remove backup files
  echo -e "\n${BLUE}Removing temporary and backup files...${RESET}"
  find_and_remove_files "*~" "Backup file"
  find_and_remove_files "*.bak" "Backup file"
  find_and_remove_files "*.tmp" "Temporary file"
  find_and_remove_files "*.swp" "Vim swap file"
  find_and_remove_files "*.swo" "Vim swap file"

  # 9. Clean up documentation and markdown files that aren't needed in production
  echo -e "\n${BLUE}Cleaning up documentation files...${RESET}"
  remove_if_exists "PRODUCTION_READINESS.md" "Pre-production documentation"
  remove_if_exists "PRODUCTION_READINESS_ASSESSMENT.md" "Pre-production documentation"
  remove_if_exists "PRODUCTION_CHECKLIST.md" "Pre-production documentation"
  remove_if_exists "SUMMARY.md" "Pre-production documentation"
  remove_if_exists "OPTIMIZATION.md" "Pre-production documentation"

  # 10. Remove cleanup related files (except this script and utility scripts)
  echo -e "\n${BLUE}Removing cleanup and standardization files...${RESET}"
  for file in $(find "${ROOT_DIR}/cleanup" -type f ! -name "production-cleanup.sh" ! -name "cleanup-report.csv" ! -name "cleanup-report.md" ! -name "complete-production-preparation.sh" ! -name "archive-and-remove-backups.sh" ! -name "update-gitignore.sh"); do
    rel_path=$(get_relative_path "$file" "$ROOT_DIR")
    remove_if_exists "$rel_path" "Cleanup utility file"
  done

  # 11. Optimize package.json (remove dev dependencies)
  # This requires a more complex operation with jq, we'll skip it in this script

  # 12. Clean up Docker artifacts
  echo -e "\n${BLUE}Cleaning up Docker artifacts...${RESET}"
  # Find and clean up development-only Docker compose files, but keep production ones
  find "${ROOT_DIR}" -name "docker-compose*.yml" ! -name "docker-compose.production*.yml" ! -name "docker-compose.yml" -type f 2>/dev/null | while read -r file; do
    rel_path=$(get_relative_path "$file" "$ROOT_DIR")
    echo -e "${YELLOW}Removing: ${file}${RESET}"
    rm -f "$file"
    log_removed "$rel_path" "Development Docker Compose file"
    update_metrics
  done

  # Generate final report
  generate_report

  echo -e "\n${GREEN}${BOLD}Cleanup completed successfully!${RESET}"
  echo -e "Detailed report available at: ${SCRIPT_DIR}/cleanup-report.md"
}

# Run the main function
main
