#!/bin/bash
# Image Tag Update Utility
# Replaces 'latest' tags with specific version numbers in Kubernetes manifests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VERSION="v1.0.0"
TARGET_DIR="kubernetes"
BACKUP=true
DRY_RUN=false
PATTERNS=(
  's|image: \(.*\):latest|image: \1:'
  's|Image: \(.*\):latest|Image: \1:'
)

# Display help
show_help() {
  echo "Image Tag Update Utility"
  echo "Usage: $0 [options]"
  echo ""
  echo "This script replaces 'latest' Docker image tags with specific version numbers"
  echo "in Kubernetes manifest files."
  echo ""
  echo "Options:"
  echo "  -h, --help                 Show this help message"
  echo "  -v, --version VERSION      Set the version number to use (default: v1.0.0)"
  echo "  -d, --directory DIR        Set the target directory (default: kubernetes)"
  echo "  --no-backup                Don't create backup files"
  echo "  --dry-run                  Run without making changes"
  echo ""
  echo "Examples:"
  echo "  $0 --version v2.1.0        # Replace 'latest' with 'v2.1.0'"
  echo "  $0 --directory k8s         # Target the 'k8s' directory"
  echo "  $0 --dry-run               # Test without making changes"
  echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -v|--version)
      VERSION="$2"
      shift 2
      ;;
    -d|--directory)
      TARGET_DIR="$2"
      shift 2
      ;;
    --no-backup)
      BACKUP=false
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}" >&2
      show_help
      exit 1
      ;;
  esac
done

# Display configuration
echo "Starting image tag update process"
echo "Target version: $VERSION"
echo "Target directory: $TARGET_DIR"
echo "Backup enabled: $BACKUP"
echo "Dry run: $DRY_RUN"
echo ""

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo -e "${RED}Target directory $TARGET_DIR does not exist!${NC}" >&2
  exit 1
fi

# Initialize counters
total_files=0
modified_files=0
updated_tags=0

# Scan directory for YAML files
echo "Scanning directory: $TARGET_DIR"

# Function to update tags in a file
update_tags() {
  local file="$1"
  local filename=$(basename "$file")
  local changes=0
  
  echo "Processing file: $file"
  
  # Check if file contains 'latest' tag
  if grep -q 'image:.*:latest' "$file" || grep -q 'Image:.*:latest' "$file"; then
    local count=$(grep -c 'image:.*:latest\|Image:.*:latest' "$file")
    echo "Found $count 'latest' tag(s) in $file"
    
    if [ "$DRY_RUN" = true ]; then
      echo -e "${YELLOW}DRY RUN: Changes to be made in $file:${NC}"
      grep -n 'image:.*:latest\|Image:.*:latest' "$file" | while read -r line; do
        line_number=$(echo "$line" | cut -d: -f1)
        line_content=$(echo "$line" | cut -d: -f2-)
        updated_line=$(echo "$line_content" | sed "s/:latest/:$VERSION/g")
        echo "  $line_content"
        echo -e "  ${GREEN}→ $updated_line${NC}"
      done
      echo ""
    else
      # Create backup if needed
      if [ "$BACKUP" = true ]; then
        cp "$file" "$file.bak"
        echo "Created backup: $file.bak"
      fi
      
      # Replace the latest tags with specific version
      sed -i "s/:latest/:$VERSION/g" "$file"
      
      echo -e "${GREEN}Updated $count image tag(s) in $file${NC}"
      modified_files=$((modified_files + 1))
      updated_tags=$((updated_tags + count))
    fi
    
    changes=1
  else
    echo "No 'latest' tags found in $file"
  fi
  
  return $changes
}

# Process YAML files recursively
find "$TARGET_DIR" -type f -name "*.yaml" -o -name "*.yml" | while read -r file; do
  total_files=$((total_files + 1))
  update_tags "$file"
done

# Display summary if not in dry run mode
if [ "$DRY_RUN" = false ]; then
  echo ""
  echo "===== Summary ====="
  echo "Files processed: $total_files"
  echo "Files modified: $modified_files"
  echo "Image tags updated: $updated_tags"
  echo "Process completed!"
else
  echo ""
  echo "===== Summary ====="
  echo "Files processed: $total_files"
  echo "Files that would be modified: $modified_files"
  echo "Image tags that would be updated: $updated_tags"
  echo "This was a DRY RUN - no files were actually modified"
  echo "Process completed!"
fi
