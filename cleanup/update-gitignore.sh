#!/bin/bash
set -e

# Enhanced .gitignore Update Script for Maily
# This script updates the .gitignore file with enhanced patterns

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
# Path to the enhanced gitignore patterns file
ENHANCED_GITIGNORE="${SCRIPT_DIR}/enhanced-gitignore.txt"
# Path to the project's gitignore file
PROJECT_GITIGNORE="${ROOT_DIR}/.gitignore"

echo -e "${BLUE}${BOLD}==================================${RESET}"
echo -e "${BLUE}${BOLD}   ENHANCED .GITIGNORE UPDATER   ${RESET}"
echo -e "${BLUE}${BOLD}==================================${RESET}"
echo ""

# Check if the enhanced gitignore file exists
if [ ! -f "$ENHANCED_GITIGNORE" ]; then
  echo -e "${RED}Error: Enhanced gitignore file not found at ${ENHANCED_GITIGNORE}${RESET}"

  # Create the file with common patterns if it doesn't exist
  echo -e "${YELLOW}Creating a default enhanced gitignore file...${RESET}"
  cat > "$ENHANCED_GITIGNORE" << 'EOF'
# Maily Enhanced .gitignore Patterns

# Backup archives
backup_archives/

# Environment files (except examples and production)
.env
.env.local
.env.development
.env.test
.env.staging

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Temporary files
*.tmp
*.temp
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Build artifacts
.next/
dist/
build/
out/
*.tsbuildinfo

# Coverage and test reports
coverage/
coverage_html/
test-reports/
test_report_*.json
test_report_*.html

# IDE specific files
.idea/
.vscode/
.cursor/
.project
.settings/
*.sublime-workspace
*.sublime-project

# Dependency directories that should be installed
node_modules/
.pnp/
.pnp.js
.venv/
venv/
env/
ENV/
.Python
env.bak/
venv.bak/

# Diagnostic and debug files
diagnostic_reports/
diagnostics/

# Docker development files (except production)
docker-compose.dev.yml
docker-compose.local.yml
docker-compose.test.yml
docker-compose.debug.yml

# Large binary files
*.tar.gz
*.zip
*.rar
*.7z
EOF

  echo -e "${GREEN}Default enhanced gitignore file created.${RESET}"
fi

# Check if the project gitignore file exists
if [ ! -f "$PROJECT_GITIGNORE" ]; then
  echo -e "${YELLOW}No .gitignore file found. Creating a new one...${RESET}"
  touch "$PROJECT_GITIGNORE"
fi

# Create a backup of the current gitignore
GITIGNORE_BACKUP="${PROJECT_GITIGNORE}.bak"
cp "$PROJECT_GITIGNORE" "$GITIGNORE_BACKUP"
echo -e "${BLUE}Created backup of current .gitignore at ${GITIGNORE_BACKUP}${RESET}"

# Display current patterns in gitignore
echo -e "\n${BLUE}Current patterns in .gitignore:${RESET}"
cat "$PROJECT_GITIGNORE" | grep -v "^$" | grep -v "^#" | sort | uniq | while read -r line; do
  echo "- $line"
done

# Display new patterns to be added
echo -e "\n${BLUE}New patterns to be added:${RESET}"
cat "$ENHANCED_GITIGNORE" | grep -v "^$" | grep -v "^#" | sort | uniq | while read -r line; do
  if ! grep -q "^$line$" "$PROJECT_GITIGNORE"; then
    echo -e "- ${GREEN}$line${RESET}"
  else
    echo -e "- ${YELLOW}$line (already exists)${RESET}"
  fi
done

# Prompt for confirmation
echo -e "\n${YELLOW}${BOLD}This script will update your .gitignore file with the patterns shown above.${RESET}"
read -p "Continue with the update? (y/n): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo -e "${YELLOW}Update canceled. Your .gitignore remains unchanged.${RESET}"
  rm "$GITIGNORE_BACKUP"
  exit 0
fi

# Add header to indicate enhanced patterns
echo -e "\n# Enhanced patterns added by update-gitignore.sh on $(date)" >> "$PROJECT_GITIGNORE"

# Add new patterns from enhanced gitignore, avoiding duplicates
cat "$ENHANCED_GITIGNORE" | grep -v "^$" | grep -v "^#" | sort | uniq | while read -r line; do
  if ! grep -q "^$line$" "$PROJECT_GITIGNORE"; then
    echo "$line" >> "$PROJECT_GITIGNORE"
  fi
done

# Sort and remove duplicate patterns, preserving comments
TEMP_GITIGNORE="$PROJECT_GITIGNORE.tmp"
cat "$PROJECT_GITIGNORE" | awk '/^#/ {print; next} /^$/ {next} !seen[$0]++' > "$TEMP_GITIGNORE"
mv "$TEMP_GITIGNORE" "$PROJECT_GITIGNORE"

echo -e "\n${GREEN}${BOLD}.gitignore file successfully updated!${RESET}"
echo -e "The following changes were made:"
echo -e "- Added new patterns from ${ENHANCED_GITIGNORE}"
echo -e "- Removed duplicate patterns"
echo -e "- Preserved comments and section headers"
echo ""
echo -e "${BLUE}If you need to revert these changes, a backup is available at:${RESET}"
echo -e "${YELLOW}${GITIGNORE_BACKUP}${RESET}"
echo -e "To revert: ${YELLOW}mv ${GITIGNORE_BACKUP} ${PROJECT_GITIGNORE}${RESET}"
