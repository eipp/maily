#!/bin/bash

# Documentation Consolidation Completion Script
#
# This script automates the complete process for finishing the documentation consolidation:
# 1. Runs link verification to check for broken references
# 2. Archives deprecated files based on the consolidation progress document
# 3. Builds the documentation portal with the updated navigation
# 4. Runs a final verification to ensure everything is working
#
# Usage: ./scripts/complete-docs-consolidation.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Maily Documentation Consolidation Completion Process ===${NC}"
echo

# Step 1: Verify documentation links
echo -e "${YELLOW}Step 1: Verifying documentation links...${NC}"
node scripts/verify-doc-links.js

if [ $? -ne 0 ]; then
  echo -e "${RED}Link verification found issues that need to be fixed before proceeding.${NC}"
  echo -e "Please fix the broken links and run this script again."
  exit 1
else
  echo -e "${GREEN}Link verification successful!${NC}"
fi

echo

# Step 2: Archive deprecated files
echo -e "${YELLOW}Step 2: Archiving deprecated files...${NC}"
node scripts/cleanup-docs.js

echo

# Step 3: Build documentation portal
echo -e "${YELLOW}Step 3: Building documentation portal...${NC}"

# Check if mkdocs is installed
if ! command -v mkdocs &> /dev/null; then
  echo -e "${RED}mkdocs is not installed. Installing...${NC}"
  pip install mkdocs mkdocs-material
fi

# Build the docs
echo "Building documentation portal with updated navigation..."
cd "$(dirname "$0")/.." # Navigate to project root
mkdocs build

if [ $? -ne 0 ]; then
  echo -e "${RED}Documentation portal build failed.${NC}"
  exit 1
else
  echo -e "${GREEN}Documentation portal built successfully!${NC}"
fi

echo

# Step 4: Final verification
echo -e "${YELLOW}Step 4: Running final verification...${NC}"
node scripts/verify-doc-links.js

if [ $? -ne 0 ]; then
  echo -e "${RED}Final verification found issues. Please fix them manually.${NC}"
  exit 1
else
  echo -e "${GREEN}Final verification successful!${NC}"
fi

echo

# Completion
echo -e "${GREEN}=== Documentation Consolidation Process Completed Successfully! ===${NC}"
echo
echo "Next steps:"
echo "1. Review the documentation portal: serve it with 'mkdocs serve'"
echo "2. Update the documentation-consolidation-progress.md to mark all tasks as completed"
echo "3. Commit the changes to the repository"
echo

exit 0
