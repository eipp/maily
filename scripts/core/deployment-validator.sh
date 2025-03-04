#!/bin/bash
# Deployment Validator
# Checks deployment configuration for issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
CONFIG_DIR="config"
VERBOSE=false

# Display help
show_help() {
  echo "Deployment Validator"
  echo "Usage: $0 [options]"
  echo ""
  echo "This script checks deployment configuration for issues."
  echo ""
  echo "Options:"
  echo "  -h, --help                 Show this help message"
  echo "  -e, --environment ENV      Set the environment (default: production)"
  echo "  -c, --config-dir DIR       Set the configuration directory (default: config)"
  echo "  -v, --verbose              Enable verbose output"
  echo ""
  echo "Examples:"
  echo "  $0 -e staging              # Validate staging configuration"
  echo "  $0 -c configs              # Use 'configs' directory"
  echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -c|--config-dir)
      CONFIG_DIR="$2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}" >&2
      show_help
      exit 1
      ;;
  esac
done

echo "=== Deployment Validator ==="
echo "Environment: $ENVIRONMENT"
echo "Configuration directory: $CONFIG_DIR"
echo ""

# Count issues for summary
issue_count=0

# Check for configuration files
echo "Checking for configuration files..."
config_files_found=0

required_config_files=(
  ".env.$ENVIRONMENT"
  "$CONFIG_DIR/config.$ENVIRONMENT.yaml"
  "$CONFIG_DIR/config.$ENVIRONMENT.json"
  "$CONFIG_DIR/.env.$ENVIRONMENT"
)

for file in "${required_config_files[@]}"; do
  if [ -f "$file" ]; then
    echo "Found configuration file: $file"
    config_files_found=$((config_files_found + 1))
  else
    echo "Missing configuration file: $file"
  fi
done

if [ $config_files_found -eq 0 ]; then
  echo -e "${RED}No configuration files found for environment $ENVIRONMENT!${NC}"
  issue_count=$((issue_count + 1))
fi

# Check for required configuration values
echo ""
echo "Checking for required configuration values..."

required_values=(
  "API_KEY"
  "SECRET_KEY"
  "SMTP_HOST"
  "SMTP_PORT"
  "SMTP_USER"
  "SMTP_PASSWORD"
  "API_ENDPOINT"
  "DOMAIN"
)

missing_values=()

if [ -f ".env.$ENVIRONMENT" ]; then
  for value in "${required_values[@]}"; do
    if ! grep -q "^$value=" ".env.$ENVIRONMENT"; then
      missing_values+=("$value")
    fi
  done
fi

if [ ${#missing_values[@]} -gt 0 ]; then
  echo "Missing required configuration values:"
  for value in "${missing_values[@]}"; do
    echo " - $value"
  done
  issue_count=$((issue_count + 1))
else
  echo "All required configuration values are present."
fi

# Check for mock data patterns
echo ""
echo "Checking for mock data patterns..."

mock_patterns=(
  "localhost"
  "example.com"
  "XXXXXXXX"
  "placeholder"
  "test"
  "mock"
  "dummy"
  "dev"
)

mock_data_found=false

# Function to check files for mock data patterns
check_file_for_mock_data() {
  local file=$1
  if [ -f "$file" ]; then
    for pattern in "${mock_patterns[@]}"; do
      if grep -q "$pattern" "$file"; then
        local matches=$(grep -n "$pattern" "$file")
        while IFS= read -r line; do
          echo " - $file: $line"
          mock_data_found=true
        done <<< "$matches"
      fi
    done
  fi
}

if [ -f ".env.$ENVIRONMENT" ]; then
  check_file_for_mock_data ".env.$ENVIRONMENT"
fi

if [ -d "$CONFIG_DIR" ]; then
  for file in "$CONFIG_DIR"/*; do
    if [[ "$file" == *"$ENVIRONMENT"* ]]; then
      check_file_for_mock_data "$file"
    fi
  done
fi

if [ -d "kubernetes" ]; then
  for file in $(find kubernetes -type f -name "*.yaml" -o -name "*.yml"); do
    check_file_for_mock_data "$file"
  done
fi

if [ "$mock_data_found" = true ]; then
  echo "Found potential mock data patterns:"
  issue_count=$((issue_count + 1))
else
  echo "No mock data patterns found."
fi

echo "IMPORTANT: Please replace all mock/test data with production values before deploying."

# Check for required Kubernetes resources
echo ""
echo "Checking for required Kubernetes resources..."

required_resources=(
  "api"
  "web"
  "email-service"
  "analytics-service"
  "workers"
  "campaign-service"
  "ai-service"
)

missing_resources=()

if [ -d "kubernetes" ]; then
  for resource in "${required_resources[@]}"; do
    found=false
    
    # Check deployments directory
    if [ -d "kubernetes/deployments" ]; then
      if ls kubernetes/deployments/*"$resource"* 1> /dev/null 2>&1; then
        found=true
      fi
    fi
    
    # Check services directory
    if [ ! "$found" = true ] && [ -d "kubernetes/services" ]; then
      if ls kubernetes/services/*"$resource"* 1> /dev/null 2>&1; then
        found=true
      fi
    fi
    
    if [ ! "$found" = true ]; then
      missing_resources+=("$resource")
    fi
  done
  
  if [ ${#missing_resources[@]} -gt 0 ]; then
    echo "Missing required resources:"
    for resource in "${missing_resources[@]}"; do
      echo " - $resource"
    done
    issue_count=$((issue_count + 1))
  else
    echo "All required Kubernetes resources are present."
  fi
else
  echo "Kubernetes directory not found. Skipping resource check."
  issue_count=$((issue_count + 1))
fi

# Check for DNS and endpoint configuration
echo ""
echo "Checking DNS and endpoint configuration..."

domain=""
if [ -f ".env.$ENVIRONMENT" ]; then
  domain=$(grep "^DOMAIN=" ".env.$ENVIRONMENT" | cut -d= -f2)
fi

if [ -z "$domain" ]; then
  echo "No domain configuration found."
  issue_count=$((issue_count + 1))
else
  echo "Domain: $domain"
fi

# Find and check API endpoints/URLs
urls=()

if [ -d "kubernetes" ]; then
  for file in $(find kubernetes -type f -name "*.yaml" -o -name "*.yml"); do
    # Extract URLs using grep
    file_urls=$(grep -o 'https\?://[^[:space:]"]*' "$file" 2>/dev/null)
    if [ ! -z "$file_urls" ]; then
      while IFS= read -r url; do
        urls+=("$url")
      done <<< "$file_urls"
    fi
  done
fi

if [ ${#urls[@]} -gt 0 ]; then
  echo "Found ${#urls[@]} API endpoints/URLs."
  
  # Check for test/staging URLs
  test_urls=0
  for url in "${urls[@]}"; do
    if [[ "$url" == *"test"* || "$url" == *"staging"* || "$url" == *"dev"* || "$url" == *"localhost"* || "$url" == *"127.0.0.1"* ]]; then
      if [ "$VERBOSE" = true ]; then
        echo " - Test URL: $url"
      fi
      test_urls=$((test_urls + 1))
    fi
  done
  
  if [ $test_urls -gt 0 ]; then
    echo "Found $test_urls test/staging URLs that should be updated for production."
    issue_count=$((issue_count + 1))
  else
    echo "All endpoints appear to be production URLs."
  fi
else
  echo "No API endpoints/URLs found."
fi

# Display validation summary
echo ""
echo "=== Validation Summary ==="
if [ $issue_count -gt 0 ]; then
  echo -e "⚠️ ${YELLOW}Missing $([ $config_files_found -eq 0 ] && echo "configuration files" || echo "${#missing_values[@]} required configuration values")${NC}"
  echo -e "⚠️ ${YELLOW}$([ "$mock_data_found" = true ] && echo "Found potential mock data that needs to be replaced" || echo "No mock data found")${NC}"
  echo -e "⚠️ ${YELLOW}$([ ${#missing_resources[@]} -gt 0 ] && echo "Missing ${#missing_resources[@]} required Kubernetes resources" || echo "All required Kubernetes resources present")${NC}"
  echo -e "⚠️ ${YELLOW}Validation completed with $issue_count issue(s) to address.${NC}"
  echo "Please fix these issues before proceeding with production deployment."
else
  echo -e "✅ ${GREEN}Validation completed successfully! No issues found.${NC}"
  echo "You can proceed with deployment."
fi
