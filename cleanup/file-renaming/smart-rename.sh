#!/bin/bash

# Smart File Renaming Utility for Maily
# This script handles identification, verification, and execution of file renaming in one process
# Usage: ./smart-rename.sh [options]
#   Options:
#     --scan-only        Only scan for candidates without renaming
#     --interactive      Interactive mode (prompts for each file)
#     --auto             Automatic mode (uses best suggestions without prompting)
#     --execute          Execute renaming after confirmation
#     --update-mapping   Update existing mapping file with new candidates
#     --help             Display this help message

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
SCAN_ONLY=false
INTERACTIVE=false
AUTO_MODE=false
EXECUTE_RENAME=false
UPDATE_MAPPING=false
MAPPING_FILE="./cleanup/file-renaming/file-mapping.md"
BACKUP_DIR=""

# Log functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

log_prompt() {
  echo -e "${CYAN}[PROMPT]${NC} $1"
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --scan-only) SCAN_ONLY=true ;;
    --interactive) INTERACTIVE=true ;;
    --auto) AUTO_MODE=true ;;
    --execute) EXECUTE_RENAME=true ;;
    --update-mapping) UPDATE_MAPPING=true ;;
    --help)
      echo "Usage: ./smart-rename.sh [options]"
      echo "Options:"
      echo "  --scan-only        Only scan for candidates without renaming"
      echo "  --interactive      Interactive mode (prompts for each file)"
      echo "  --auto             Automatic mode (uses best suggestions without prompting)"
      echo "  --execute          Execute renaming after confirmation"
      echo "  --update-mapping   Update existing mapping file with new candidates"
      echo "  --help             Display this help message"
      exit 0
      ;;
    *) log_error "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

# Validate options
if [ "$INTERACTIVE" == "true" ] && [ "$AUTO_MODE" == "true" ]; then
  log_error "Cannot use both --interactive and --auto modes"
  exit 1
fi

if [ "$SCAN_ONLY" == "true" ] && [ "$EXECUTE_RENAME" == "true" ]; then
  log_error "Cannot use both --scan-only and --execute options"
  exit 1
fi

if [ "$EXECUTE_RENAME" == "true" ] && [ "$INTERACTIVE" == "false" ] && [ "$AUTO_MODE" == "false" ]; then
  log_error "Must specify either --interactive or --auto with --execute"
  exit 1
fi

# Common versioning qualifiers to search for
QUALIFIERS=(
  "enhanced"
  "optimized"
  "improved"
  "virtualized"
  "advanced"
  "upgraded"
  "v2"
  "v3"
)

# Directories to search
SEARCH_DIRS=(
  "./apps"
  "./infrastructure"
  "./tests"
  "./packages"
  "./libs"
  "./docs"
)

# File extensions to include
FILE_EXTENSIONS=(
  "ts"
  "tsx"
  "js"
  "jsx"
  "py"
  "md"
  "yaml"
  "yml"
)

# Function to suggest a standardized name by removing qualifiers
suggest_standardized_name() {
  local file_path="$1"
  local qualifier="$2"

  # Get the directory and filename
  local dir=$(dirname "$file_path")
  local filename=$(basename "$file_path")
  local extension="${filename##*.}"
  local basename="${filename%.*}"

  # Remove the qualifier from the basename
  local new_basename
  case "$basename" in
    *"_$qualifier"*)
      new_basename="${basename/_$qualifier/}"
      ;;
    *"$qualifier"_*)
      new_basename="${basename/$qualifier_/}"
      ;;
    *"-$qualifier"*)
      new_basename="${basename/-$qualifier/}"
      ;;
    *"$qualifier"-*)
      new_basename="${basename/$qualifier-/}"
      ;;
    *"$qualifier"*)
      new_basename="${basename/$qualifier/}"
      ;;
    *)
      new_basename="$basename"
      ;;
  esac

  # Special case for test files
  if [[ "$basename" == "test_"*"$qualifier"* ]]; then
    new_basename="${basename/test_$qualifier/test}"
  fi

  # Return the new standardized path
  echo "$dir/$new_basename.$extension"
}

# Function to check if a file exists
check_file_exists() {
  local file_path="$1"
  if [ -f "$file_path" ]; then
    return 0
  else
    return 1
  fi
}

# Function to count references to a file
count_references() {
  local file_name="$1"
  local count=0

  # Count references in all relevant files
  count=$(find ./apps ./infrastructure ./tests -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" \) -exec grep -l "$file_name" {} \; | wc -l)

  echo "$count"
}

# Function to categorize a file
categorize_file() {
  local file_path="$1"

  if [[ "$file_path" == *"/components/"* ]]; then
    echo "Canvas Components"
  elif [[ "$file_path" == *"/hooks/"* || "$file_path" == *"/lib/"* ]]; then
    echo "Hooks and Libraries"
  elif [[ "$file_path" == *"/services/"* ]]; then
    echo "API Services"
  elif [[ "$file_path" == *"/ai/adapters/"* || "$file_path" == *"/ai/orchestration/"* ]]; then
    echo "AI Adapters"
  elif [[ "$file_path" == *"/test"* || "$file_path" == *"/__tests__/"* ]]; then
    echo "Tests"
  elif [[ "$file_path" == *"/infrastructure/"* || "$file_path" == *"/kubernetes/"* ]]; then
    echo "Infrastructure"
  else
    echo "Other"
  fi
}

# Function to backup a file
backup_file() {
  local file_path="$1"
  local timestamp=$(date +"%Y%m%d%H%M%S")

  # Create backup directory if it doesn't exist
  if [ -z "$BACKUP_DIR" ]; then
    BACKUP_DIR="./cleanup/file-renaming/backups/$timestamp"
    mkdir -p "$BACKUP_DIR"
  fi

  # Create directory structure in backup
  local relative_dir=$(dirname "$file_path")
  mkdir -p "$BACKUP_DIR/$relative_dir"

  # Copy file to backup
  cp "$file_path" "$BACKUP_DIR/$file_path"
  log_info "Backed up: $file_path to $BACKUP_DIR/$file_path"
}

# Function to rename a file and update references
rename_file() {
  local old_path="$1"
  local new_path="$2"
  local category="$3"
  local description="$4"

  # Check if the file exists
  if ! check_file_exists "$old_path"; then
    log_error "File not found: $old_path"
    return 1
  fi

  # Check if the destination already exists and is different
  if check_file_exists "$new_path" && ! cmp -s "$old_path" "$new_path"; then
    log_error "Destination file already exists and is different: $new_path"
    return 1
  fi

  # Create backup of the file
  backup_file "$old_path"

  # Create directory for new file if it doesn't exist
  mkdir -p "$(dirname "$new_path")"

  # Rename the file
  mv "$old_path" "$new_path"
  log_success "Renamed: $old_path -> $new_path"

  # Update references in the codebase
  log_info "Updating references from $old_path to $new_path..."

  # Get the file names without paths
  local old_name=$(basename "$old_path")
  local new_name=$(basename "$new_path")

  # Get the relative import path (without extension)
  local old_import_path="${old_path%.*}"
  local new_import_path="${new_path%.*}"

  # Remove apps/ or other common prefixes for import statements
  old_import_path=$(echo "$old_import_path" | sed 's|^apps/||')
  new_import_path=$(echo "$new_import_path" | sed 's|^apps/||')

  # Find and replace references in all relevant files
  find ./apps -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" \) -exec grep -l "$old_name" {} \; | while read -r file; do
    # Create backup of the file
    backup_file "$file"

    # Replace references to the file
    cat "$file" | sed "s|$old_name|$new_name|g" > "${file}.tmp"
    mv "${file}.tmp" "$file"

    # Replace import statements (for TypeScript/JavaScript)
    if [[ "$file" =~ \.(ts|tsx|js|jsx)$ ]]; then
      cat "$file" | sed "s|from ['\"].*/$old_name['\"]|from './$new_name'|g" > "${file}.tmp"
      mv "${file}.tmp" "$file"
      cat "$file" | sed "s|from ['\"].*/$old_import_path['\"]|from './$new_import_path'|g" > "${file}.tmp"
      mv "${file}.tmp" "$file"
      cat "$file" | sed "s|import ['\"].*/$old_import_path['\"]|import './$new_import_path'|g" > "${file}.tmp"
      mv "${file}.tmp" "$file"
    fi

    # Replace Python imports
    if [[ "$file" =~ \.py$ ]]; then
      cat "$file" | sed "s|from $old_import_path import|from $new_import_path import|g" > "${file}.tmp"
      mv "${file}.tmp" "$file"
      cat "$file" | sed "s|import $old_import_path|import $new_import_path|g" > "${file}.tmp"
      mv "${file}.tmp" "$file"
    fi
  done

  # Update index files if they exist
  local index_file="$(dirname "$old_path")/index.ts"
  if [ -f "$index_file" ]; then
    backup_file "$index_file"
    cat "$index_file" | sed "s|$old_name|$new_name|g" > "${index_file}.tmp"
    mv "${index_file}.tmp" "$index_file"
    log_success "Updated index file: $index_file"
  fi

  # Add to mapping file
  add_to_mapping "$old_path" "$new_path" "$category" "$description"

  return 0
}

# Function to verify file existence
verify_file_exists() {
  local file_path="$1"
  if check_file_exists "$file_path"; then
    log_success "File exists: $file_path"
    return 0
  else
    log_error "File not found: $file_path"
    return 1
  fi
}

# Function to verify file does not exist
verify_file_not_exists() {
  local file_path="$1"
  if ! check_file_exists "$file_path"; then
    log_success "File does not exist: $file_path"
    return 0
  else
    log_error "File still exists: $file_path"
    return 1
  fi
}

# Function to add a file mapping to the mapping file
add_to_mapping() {
  local old_path="$1"
  local new_path="$2"
  local category="$3"
  local description="$4"

  # Initialize the mapping file if it doesn't exist or we're not updating
  if [ ! -f "$MAPPING_FILE" ] || [ "$UPDATE_MAPPING" == "false" ]; then
    # Create directory for mapping file if it doesn't exist
    mkdir -p "$(dirname "$MAPPING_FILE")"

    # Create or overwrite the mapping file with headers
    cat > "$MAPPING_FILE" << EOF
# File Renaming Mapping

This document maps files with versioning qualifiers to their new standardized names.

EOF
  fi

  # Check if the category section exists in the mapping file
  if ! grep -q "^## $category" "$MAPPING_FILE"; then
    # Add category section
    cat >> "$MAPPING_FILE" << EOF

## $category

| Original File | New Standardized Name | Description |
|---------------|----------------------|-------------|
EOF
  fi

  # Add entry to the mapping file under the appropriate category
  grep -v "^| \`$old_path\`" "$MAPPING_FILE" > "${MAPPING_FILE}.tmp"
  mv "${MAPPING_FILE}.tmp" "$MAPPING_FILE"

  # Append the new entry after the header - using a more compatible approach
  awk -v old="$old_path" -v new="$new_path" -v desc="$description" '
    /^## '"$category"'/ { print; in_section=1; next }
    /^## / { in_section=0 }
    in_section && /^| Original File/ {
      print;
      print "| `" old "` | `" new "` | " desc " |";
      next
    }
    { print }
  ' "$MAPPING_FILE" > "${MAPPING_FILE}.tmp" && mv "${MAPPING_FILE}.tmp" "$MAPPING_FILE"
}

# Function to scan for files matching the qualifiers
scan_files() {
  local candidates=()
  local count=0
  local total_candidates=0

  log_info "Starting scan for files with versioning qualifiers..."

  # Search for files matching the qualifiers in each directory
  for dir in "${SEARCH_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
      log_warning "Directory $dir does not exist, skipping..."
      continue
    fi

    log_info "Scanning directory: $dir"

    # Build the find command extensions part
    EXTENSIONS_PATTERN=""
    for ext in "${FILE_EXTENSIONS[@]}"; do
      if [ -z "$EXTENSIONS_PATTERN" ]; then
        EXTENSIONS_PATTERN="-name \"*.$ext\""
      else
        EXTENSIONS_PATTERN="$EXTENSIONS_PATTERN -o -name \"*.$ext\""
      fi
    done

    # Search for each qualifier
    for qualifier in "${QUALIFIERS[@]}"; do
      count=0

      # Find files with the qualifier in the name
      while IFS= read -r file; do
        if [ -n "$file" ]; then
          candidates+=("$file:$qualifier")
          ((count++))
        fi
      done < <(find "$dir" -type f \( -name "*_${qualifier}*.*" -o -name "*${qualifier}_*.*" -o -name "*-${qualifier}*.*" -o -name "*${qualifier}-*.*" -o -name "*${qualifier}*.*" \) | grep -v "node_modules" | grep -v ".git")

      if [ $count -gt 0 ]; then
        log_success "Found $count files with qualifier '$qualifier'"
        ((total_candidates += count))
      fi
    done
  done

  log_success "Scan completed! Found $total_candidates potential files for renaming."

  # Process candidates
  if [ ${#candidates[@]} -gt 0 ]; then
    log_info "Processing ${#candidates[@]} candidates..."
    echo ""

    local renamed_count=0
    local skipped_count=0
    local error_count=0

    for candidate in "${candidates[@]}"; do
      local file_path="${candidate%%:*}"
      local qualifier="${candidate#*:}"

      # Suggest standardized name
      local suggested_name=$(suggest_standardized_name "$file_path" "$qualifier")

      # Count references
      local ref_count=$(count_references "$(basename "$file_path")")

      # Categorize the file
      local category=$(categorize_file "$file_path")

      # Determine confidence level
      local confidence="High"
      if [[ "$file_path" == *"$qualifier"* && "$suggested_name" == *"$qualifier"* ]]; then
        confidence="Low"
      fi

      # Display candidate information
      echo "File: $file_path"
      echo "Suggested new name: $suggested_name"
      echo "Qualifier: $qualifier"
      echo "Confidence: $confidence"
      echo "References: $ref_count"
      echo "Category: $category"
      echo ""

      local description="$qualifier version should become the standard"
      local proceed=false
      local custom_name=""

      if [ "$SCAN_ONLY" == "true" ]; then
        # Skip renaming in scan-only mode
        ((skipped_count++))
      elif [ "$AUTO_MODE" == "true" ]; then
        # Auto mode - use suggested name if confidence is high
        if [ "$confidence" == "High" ]; then
          proceed=true
        else
          log_warning "Skipping low confidence suggestion"
          ((skipped_count++))
        fi
      elif [ "$INTERACTIVE" == "true" ]; then
        # Interactive mode - prompt for confirmation
        log_prompt "What would you like to do? (y)es/(n)o/(c)ustom: "
        read -r choice

        case "$choice" in
          y|Y)
            proceed=true
            ;;
          c|C)
            log_prompt "Enter custom new name: "
            read -r custom_name
            if [ -n "$custom_name" ]; then
              suggested_name="$custom_name"
              proceed=true
            else
              log_warning "No custom name provided, skipping"
              ((skipped_count++))
            fi
            ;;
          *)
            log_warning "Skipped by user"
            ((skipped_count++))
            ;;
        esac
      else
        # Default - just add to mapping without renaming
        add_to_mapping "$file_path" "$suggested_name" "$category" "$description"
        ((skipped_count++))
      fi

      # Execute renaming if confirmed
      if [ "$proceed" == "true" ] && [ "$EXECUTE_RENAME" == "true" ]; then
        if rename_file "$file_path" "$suggested_name" "$category" "$description"; then
          ((renamed_count++))
        else
          ((error_count++))
        fi
      elif [ "$proceed" == "true" ]; then
        # Just add to mapping without renaming
        add_to_mapping "$file_path" "$suggested_name" "$category" "$description"
        ((skipped_count++))
      fi
    done

    # Display summary
    echo "=============================================="
    echo "Summary:"
    echo "=============================================="
    echo "Total candidates: ${#candidates[@]}"
    echo "Files renamed: $renamed_count"
    echo "Files skipped: $skipped_count"
    echo "Errors: $error_count"
    echo ""

    if [ "$SCAN_ONLY" == "true" ]; then
      log_info "Scan-only mode, no files were renamed."
    elif [ "$EXECUTE_RENAME" == "false" ]; then
      log_info "Dry-run mode, no files were renamed."
    fi

    log_info "Mapping file updated: $MAPPING_FILE"
  else
    log_warning "No files found matching the criteria."
  fi
}

# Display header
echo "========================================================"
echo "  Maily Smart File Renaming Utility"
echo "========================================================"
echo ""

# Run the scan
scan_files

# If executing rename, verify afterwards
if [ "$EXECUTE_RENAME" == "true" ]; then
  echo ""
  log_info "Verifying renamed files..."

  # Import the verify-renaming.sh functionality here if needed
  # For now, we'll just check for the existence of the new files

  errors=0
  while IFS= read -r line; do
    old_path="${line% -> *}"
    new_path="${line#* -> }"

    # Verify old file doesn't exist
    if verify_file_exists "$old_path"; then
      log_error "Old file still exists: $old_path"
      errors=$((errors + 1))
    fi

    # Verify new file exists
    if ! verify_file_exists "$new_path"; then
      log_error "New file doesn't exist: $new_path"
      errors=$((errors + 1))
    fi
  done < <(cat "$result_file")

  if [ $errors -eq 0 ]; then
    log_success "Verification completed successfully!"
  else
    log_error "Verification completed with $errors errors."
  fi
fi

# Generate final report if needed
if [ "$EXECUTE_RENAME" == "true" ]; then
  echo ""
  log_info "Operation completed. Files renamed and verified."
  log_info "Backup of original files created at: $BACKUP_DIR"
  log_info "Please run tests to ensure everything works correctly."
fi
