#!/bin/bash
# deploy-cloudflare-waf.sh
# Script to deploy WAF rules to CloudFlare

set -e

# Check if the WAF rules file exists
if [ ! -f infrastructure/cloudflare/waf-rules.json ]; then
  echo "Error: WAF rules file not found at infrastructure/cloudflare/waf-rules.json"
  exit 1
fi

# Check if the CloudFlare API token is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "Error: CLOUDFLARE_API_TOKEN environment variable is not set."
  echo "Please set it with your CloudFlare API token."
  exit 1
fi

# Check if the CloudFlare zone ID is set
if [ -z "$CLOUDFLARE_ZONE_ID" ]; then
  echo "Error: CLOUDFLARE_ZONE_ID environment variable is not set."
  echo "Please set it with your CloudFlare zone ID."
  exit 1
fi

# CloudFlare API endpoint
API_ENDPOINT="https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/firewall/rules"

# Function to create or update a WAF rule
deploy_rule() {
  local rule_id=$1
  local description=$2
  local expression=$3
  local action=$4
  local enabled=$5
  local rate_limit=$6

  # Check if the rule already exists
  existing_rule=$(curl -s -X GET "$API_ENDPOINT?id=$rule_id" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json")
  
  # Extract the result count to determine if the rule exists
  result_count=$(echo $existing_rule | jq -r '.result_info.count')
  
  if [ "$result_count" -gt 0 ]; then
    echo "Updating existing rule: $description"
    
    # Extract the existing rule ID from the response
    existing_rule_id=$(echo $existing_rule | jq -r '.result[0].id')
    
    # Prepare the payload for updating the rule
    if [ -n "$rate_limit" ]; then
      payload=$(jq -n \
        --arg id "$existing_rule_id" \
        --arg description "$description" \
        --arg expression "$expression" \
        --arg action "$action" \
        --argjson enabled $enabled \
        --argjson rate_limit "$rate_limit" \
        '{
          "id": $id,
          "description": $description,
          "expression": $expression,
          "action": $action,
          "enabled": $enabled,
          "rate_limit": $rate_limit
        }')
    else
      payload=$(jq -n \
        --arg id "$existing_rule_id" \
        --arg description "$description" \
        --arg expression "$expression" \
        --arg action "$action" \
        --argjson enabled $enabled \
        '{
          "id": $id,
          "description": $description,
          "expression": $expression,
          "action": $action,
          "enabled": $enabled
        }')
    fi
    
    # Update the rule
    response=$(curl -s -X PUT "$API_ENDPOINT/$existing_rule_id" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" \
      --data "$payload")
    
  else
    echo "Creating new rule: $description"
    
    # Prepare the payload for creating a new rule
    if [ -n "$rate_limit" ]; then
      payload=$(jq -n \
        --arg id "$rule_id" \
        --arg description "$description" \
        --arg expression "$expression" \
        --arg action "$action" \
        --argjson enabled $enabled \
        --argjson rate_limit "$rate_limit" \
        '{
          "id": $id,
          "description": $description,
          "expression": $expression,
          "action": $action,
          "enabled": $enabled,
          "rate_limit": $rate_limit
        }')
    else
      payload=$(jq -n \
        --arg id "$rule_id" \
        --arg description "$description" \
        --arg expression "$expression" \
        --arg action "$action" \
        --argjson enabled $enabled \
        '{
          "id": $id,
          "description": $description,
          "expression": $expression,
          "action": $action,
          "enabled": $enabled
        }')
    fi
    
    # Create the rule
    response=$(curl -s -X POST "$API_ENDPOINT" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" \
      --data "$payload")
  fi
  
  # Check if the operation was successful
  success=$(echo $response | jq -r '.success')
  
  if [ "$success" = "true" ]; then
    echo "Successfully deployed rule: $description"
  else
    echo "Failed to deploy rule: $description"
    echo "Error: $(echo $response | jq -r '.errors')"
    exit 1
  fi
}

# Parse the WAF rules file and deploy each rule
echo "Deploying WAF rules to CloudFlare..."
rules=$(jq -c '.rules[]' infrastructure/cloudflare/waf-rules.json)

while IFS= read -r rule; do
  rule_id=$(echo $rule | jq -r '.id')
  description=$(echo $rule | jq -r '.description')
  expression=$(echo $rule | jq -r '.expression')
  action=$(echo $rule | jq -r '.action')
  enabled=$(echo $rule | jq -r '.enabled')
  
  # Check if the rule has rate_limit configuration
  if echo $rule | jq -e '.rate_limit' > /dev/null; then
    rate_limit=$(echo $rule | jq -c '.rate_limit')
    deploy_rule "$rule_id" "$description" "$expression" "$action" "$enabled" "$rate_limit"
  else
    deploy_rule "$rule_id" "$description" "$expression" "$action" "$enabled" ""
  fi
done <<< "$rules"

echo "WAF rules deployment completed successfully!"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

