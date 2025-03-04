#!/bin/bash
# Configuration Collector
# Interactively collects configuration values and saves them to the appropriate file

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
OUTPUT_FILE=""
FORMAT="env"

# Display help
show_help() {
  echo "Configuration Collector"
  echo "Usage: $0 [options]"
  echo ""
  echo "This script interactively collects configuration values and saves them to the appropriate file."
  echo ""
  echo "Options:"
  echo "  -h, --help                 Show this help message"
  echo "  -e, --environment ENV      Set the environment (default: production)"
  echo "  -o, --output FILE          Set the output file (default: .env.ENV)"
  echo "  -f, --format FORMAT        Set the format (env, json, yaml) (default: env)"
  echo ""
  echo "Examples:"
  echo "  $0 -e staging              # Collect configuration for staging"
  echo "  $0 -o config.env           # Save to config.env"
  echo "  $0 -f json                 # Save in JSON format"
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
    -o|--output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -f|--format)
      FORMAT="$2"
      if [[ ! "$FORMAT" =~ ^(env|json|yaml)$ ]]; then
        echo -e "${RED}Invalid format: $FORMAT. Must be env, json, or yaml.${NC}" >&2
        exit 1
      fi
      shift 2
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}" >&2
      show_help
      exit 1
      ;;
  esac
done

# Set default output file if not provided
if [ -z "$OUTPUT_FILE" ]; then
  OUTPUT_FILE=".env.$ENVIRONMENT"
fi

echo "=== Configuration Collector ==="
echo "Environment: $ENVIRONMENT"
echo "Output file: $OUTPUT_FILE"
echo "Format: $FORMAT"
echo ""

# Define required configuration values
declare -A config_descriptions=(
  ["DATABASE_URL"]="Database connection string (e.g., postgres://user:password@hostname:port/database)"
  ["API_KEY"]="API key for external services"
  ["SECRET_KEY"]="Secret key for your application"
  ["JWT_SECRET"]="Secret for JWT token generation"
  ["SMTP_HOST"]="SMTP server hostname"
  ["SMTP_PORT"]="SMTP server port (e.g., 25, 465, 587)"
  ["SMTP_USER"]="SMTP username"
  ["SMTP_PASSWORD"]="SMTP password"
  ["REDIS_URL"]="Redis connection string"
  ["API_ENDPOINT"]="External API endpoint"
  ["DOMAIN"]="Main domain for the application"
  ["STORAGE_BUCKET"]="Cloud storage bucket name"
  ["CDN_URL"]="Content delivery network URL"
  ["LOG_LEVEL"]="Logging level (debug, info, warn, error)"
  ["APP_NAME"]="Application name"
  ["WEB_API_BASE_URL"]="Web API base URL"
  ["EMAIL_SERVICE_API_KEY"]="Email service API key"
  ["ANALYTICS_API_ENDPOINT"]="Analytics service endpoint"
  ["AI_SERVICE_MODEL_VERSION"]="AI service model version"
  ["CAMPAIGN_SERVICE_MAX_THREADS"]="Maximum threads for campaign service"
  ["K8S_INGRESS_HOST"]="Kubernetes ingress host"
  ["K8S_TLS_SECRET_NAME"]="Kubernetes TLS secret name"
  ["K8S_NAMESPACE"]="Kubernetes namespace"
  ["K8S_STORAGE_CLASS"]="Kubernetes storage class"
  ["K8S_REGISTRY_SECRET"]="Kubernetes registry secret"
)

# Sensitive values that should be hidden when entered
sensitive_values=(
  "API_KEY"
  "SECRET_KEY"
  "JWT_SECRET"
  "SMTP_PASSWORD"
  "EMAIL_SERVICE_API_KEY"
  "K8S_TLS_SECRET_NAME"
  "K8S_REGISTRY_SECRET"
)

# Read existing configuration
declare -A config_values
if [ -f "$OUTPUT_FILE" ]; then
  while IFS='=' read -r key value || [ -n "$key" ]; do
    # Skip comments and empty lines
    [[ $key =~ ^# ]] || [ -z "$key" ] && continue
    
    # Strip quotes from value if present
    value="${value%\"}"
    value="${value#\"}"
    
    config_values["$key"]="$value"
  done < "$OUTPUT_FILE"
fi

# Function to check if a value is sensitive
is_sensitive() {
  local key="$1"
  for sensitive_key in "${sensitive_values[@]}"; do
    if [ "$key" = "$sensitive_key" ]; then
      return 0
    fi
  done
  return 1
}

# Collect configuration values
echo "Collecting configuration values..."

for key in "${!config_descriptions[@]}"; do
  description="${config_descriptions[$key]}"
  
  if [ -n "${config_values[$key]}" ]; then
    if is_sensitive "$key"; then
      echo -e "✓ $key (value set securely)"
    else
      echo -e "✓ $key (already set)"
    fi
    continue
  fi
  
  if is_sensitive "$key"; then
    # Collect sensitive value securely
    echo -n "Enter value for $key: "
    read -s value
    echo ""
    
    if [ -z "$value" ]; then
      echo -e "${YELLOW}Warning: No value provided for $key${NC}"
      continue
    fi
    
    config_values["$key"]="$value"
    echo -e "✓ $key (value set securely)"
  else
    # Collect normal value
    echo -n "Enter value for $key: "
    read value
    
    if [ -z "$value" ]; then
      echo -e "${YELLOW}Warning: No value provided for $key${NC}"
      continue
    fi
    
    config_values["$key"]="$value"
    echo -e "✓ $key = $value"
  fi
done

# Ask if user wants to add additional values
echo ""
read -p "Do you want to add additional configuration values? (y/n) " add_more

if [[ "$add_more" =~ ^[Yy]$ ]]; then
  while true; do
    echo -n "Enter key (or leave empty to finish): "
    read key
    
    if [ -z "$key" ]; then
      break
    fi
    
    if is_sensitive "$key"; then
      echo -n "Enter value for $key: "
      read -s value
      echo ""
    else
      echo -n "Enter value for $key: "
      read value
    fi
    
    config_values["$key"]="$value"
    
    if is_sensitive "$key"; then
      echo -e "✓ $key (value set securely)"
    else
      echo -e "✓ $key = $value"
    fi
  done
fi

# Save configuration to file
echo ""
echo "Configuration collection complete!"

case "$FORMAT" in
  env)
    # Save as .env file
    {
      echo "# Configuration generated by config-collector.sh"
      echo "# Environment: $ENVIRONMENT"
      echo "# Generated at: $(date)"
      echo ""
      
      for key in "${!config_values[@]}"; do
        echo "$key=${config_values[$key]}"
      done
    } > "$OUTPUT_FILE"
    ;;
    
  json)
    # Save as JSON file
    {
      echo "{"
      first=true
      
      for key in "${!config_values[@]}"; do
        if [ "$first" = true ]; then
          first=false
        else
          echo ","
        fi
        
        # Escape double quotes in value
        value="${config_values[$key]//\"/\\\"}"
        
        echo -n "  \"$key\": \"$value\""
      done
      
      echo ""
      echo "}"
    } > "$OUTPUT_FILE"
    ;;
    
  yaml)
    # Save as YAML file
    {
      echo "# Configuration generated by config-collector.sh"
      echo "# Environment: $ENVIRONMENT"
      echo "# Generated at: $(date)"
      echo ""
      
      for key in "${!config_values[@]}"; do
        # Escape special characters in value
        value="${config_values[$key]}"
        if [[ "$value" =~ [:#\[\]{}|>*&!%@\`,] || "$value" =~ ^[0-9] ]]; then
          # Need to quote the value
          echo "$key: \"${value//\"/\\\"}\""
        else
          echo "$key: $value"
        fi
      done
    } > "$OUTPUT_FILE"
    ;;
esac

echo "Configuration saved to: $OUTPUT_FILE"
echo ""
echo "REMINDER: For Kubernetes deployments remember to:"
echo "1. Create Kubernetes secrets for sensitive values"
echo "2. Update Kubernetes manifests to reference these secrets"
echo "3. Run the deployment validator to check configuration completeness"
echo ""
echo "Example commands:"
echo "  kubectl create secret generic maily-secrets --from-env-file=$OUTPUT_FILE -n $ENVIRONMENT"
echo "  ./scripts/deployment-validator.sh -e $ENVIRONMENT"
