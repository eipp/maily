#!/bin/bash
# Setup script for Auth0 and OPA integration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Auth0 and OPA for Maily...${NC}"

# Check if required tools are installed
command -v curl >/dev/null 2>&1 || { echo -e "${RED}Error: curl is required but not installed. Please install curl and try again.${NC}" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Error: jq is required but not installed. Please install jq and try again.${NC}" >&2; exit 1; }

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo -e "${GREEN}Loaded environment variables from .env${NC}"
else
  echo -e "${YELLOW}Warning: .env file not found. Using default values.${NC}"
fi

# Check if required environment variables are set
if [ -z "$AUTH0_DOMAIN" ] || [ -z "$AUTH0_CLIENT_ID" ] || [ -z "$AUTH0_CLIENT_SECRET" ]; then
  echo -e "${RED}Error: AUTH0_DOMAIN, AUTH0_CLIENT_ID, and AUTH0_CLIENT_SECRET must be set in .env file.${NC}"
  exit 1
fi

echo -e "${GREEN}Configuring Auth0...${NC}"

# Get Auth0 Management API token
echo "Getting Auth0 Management API token..."
AUTH0_TOKEN=$(curl --request POST \
  --url "https://${AUTH0_DOMAIN}/oauth/token" \
  --header 'content-type: application/json' \
  --data "{\"client_id\":\"${AUTH0_CLIENT_ID}\",\"client_secret\":\"${AUTH0_CLIENT_SECRET}\",\"audience\":\"https://${AUTH0_DOMAIN}/api/v2/\",\"grant_type\":\"client_credentials\"}" | jq -r '.access_token')

if [ -z "$AUTH0_TOKEN" ] || [ "$AUTH0_TOKEN" == "null" ]; then
  echo -e "${RED}Error: Failed to get Auth0 Management API token.${NC}"
  exit 1
fi

echo "Auth0 Management API token obtained successfully."

# Create Auth0 roles
echo "Creating Auth0 roles..."
ROLES=("admin" "editor" "viewer" "analyst")

for ROLE in "${ROLES[@]}"; do
  echo "Creating role: $ROLE"
  ROLE_RESPONSE=$(curl --request POST \
    --url "https://${AUTH0_DOMAIN}/api/v2/roles" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"name\":\"${ROLE}\",\"description\":\"${ROLE} role for Maily\"}")

  ROLE_ID=$(echo $ROLE_RESPONSE | jq -r '.id')

  if [ -z "$ROLE_ID" ] || [ "$ROLE_ID" == "null" ]; then
    echo -e "${YELLOW}Warning: Role '${ROLE}' may already exist or could not be created.${NC}"
  else
    echo "Role '${ROLE}' created with ID: ${ROLE_ID}"
  fi
done

# Create Auth0 API permissions
echo "Creating Auth0 API permissions..."

# Get the API ID
API_ID=$(curl --request GET \
  --url "https://${AUTH0_DOMAIN}/api/v2/resource-servers" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" | jq -r ".[] | select(.identifier==\"${AUTH0_API_AUDIENCE}\") | .id")

if [ -z "$API_ID" ] || [ "$API_ID" == "null" ]; then
  echo "Creating API..."
  API_RESPONSE=$(curl --request POST \
    --url "https://${AUTH0_DOMAIN}/api/v2/resource-servers" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"name\":\"Maily API\",\"identifier\":\"${AUTH0_API_AUDIENCE}\",\"signing_alg\":\"RS256\",\"token_lifetime\":86400,\"skip_consent_for_verifiable_first_party_clients\":true}")

  API_ID=$(echo $API_RESPONSE | jq -r '.id')

  if [ -z "$API_ID" ] || [ "$API_ID" == "null" ]; then
    echo -e "${RED}Error: Failed to create API.${NC}"
    exit 1
  fi

  echo "API created with ID: ${API_ID}"
else
  echo "API already exists with ID: ${API_ID}"
fi

# Define permissions
PERMISSIONS=(
  "read:campaigns"
  "write:campaigns"
  "read:templates"
  "write:templates"
  "read:analytics"
  "read:users"
  "write:users"
  "read:settings"
  "write:settings"
)

# Add permissions to API
echo "Adding permissions to API..."
for PERMISSION in "${PERMISSIONS[@]}"; do
  echo "Adding permission: $PERMISSION"
  PERMISSION_RESPONSE=$(curl --request PATCH \
    --url "https://${AUTH0_DOMAIN}/api/v2/resource-servers/${API_ID}" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"scopes\":[{\"value\":\"${PERMISSION}\",\"description\":\"${PERMISSION} permission\"}]}")
done

# Assign permissions to roles
echo "Assigning permissions to roles..."

# Admin role gets all permissions
ADMIN_ROLE_ID=$(curl --request GET \
  --url "https://${AUTH0_DOMAIN}/api/v2/roles" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" | jq -r ".[] | select(.name==\"admin\") | .id")

if [ -n "$ADMIN_ROLE_ID" ] && [ "$ADMIN_ROLE_ID" != "null" ]; then
  echo "Assigning all permissions to admin role..."
  PERMISSIONS_JSON="["
  for PERMISSION in "${PERMISSIONS[@]}"; do
    PERMISSIONS_JSON="${PERMISSIONS_JSON}{\"permission_name\":\"${PERMISSION}\",\"resource_server_identifier\":\"${AUTH0_API_AUDIENCE}\"},"
  done
  PERMISSIONS_JSON="${PERMISSIONS_JSON%,}]"

  curl --request POST \
    --url "https://${AUTH0_DOMAIN}/api/v2/roles/${ADMIN_ROLE_ID}/permissions" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"permissions\":${PERMISSIONS_JSON}}"

  echo "Permissions assigned to admin role."
else
  echo -e "${YELLOW}Warning: Admin role not found.${NC}"
fi

# Editor role gets write:campaigns, write:templates, read:campaigns, read:templates
EDITOR_ROLE_ID=$(curl --request GET \
  --url "https://${AUTH0_DOMAIN}/api/v2/roles" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" | jq -r ".[] | select(.name==\"editor\") | .id")

if [ -n "$EDITOR_ROLE_ID" ] && [ "$EDITOR_ROLE_ID" != "null" ]; then
  echo "Assigning permissions to editor role..."
  EDITOR_PERMISSIONS=("write:campaigns" "write:templates" "read:campaigns" "read:templates")
  PERMISSIONS_JSON="["
  for PERMISSION in "${EDITOR_PERMISSIONS[@]}"; do
    PERMISSIONS_JSON="${PERMISSIONS_JSON}{\"permission_name\":\"${PERMISSION}\",\"resource_server_identifier\":\"${AUTH0_API_AUDIENCE}\"},"
  done
  PERMISSIONS_JSON="${PERMISSIONS_JSON%,}]"

  curl --request POST \
    --url "https://${AUTH0_DOMAIN}/api/v2/roles/${EDITOR_ROLE_ID}/permissions" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"permissions\":${PERMISSIONS_JSON}}"

  echo "Permissions assigned to editor role."
else
  echo -e "${YELLOW}Warning: Editor role not found.${NC}"
fi

# Viewer role gets read:campaigns, read:templates
VIEWER_ROLE_ID=$(curl --request GET \
  --url "https://${AUTH0_DOMAIN}/api/v2/roles" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" | jq -r ".[] | select(.name==\"viewer\") | .id")

if [ -n "$VIEWER_ROLE_ID" ] && [ "$VIEWER_ROLE_ID" != "null" ]; then
  echo "Assigning permissions to viewer role..."
  VIEWER_PERMISSIONS=("read:campaigns" "read:templates")
  PERMISSIONS_JSON="["
  for PERMISSION in "${VIEWER_PERMISSIONS[@]}"; do
    PERMISSIONS_JSON="${PERMISSIONS_JSON}{\"permission_name\":\"${PERMISSION}\",\"resource_server_identifier\":\"${AUTH0_API_AUDIENCE}\"},"
  done
  PERMISSIONS_JSON="${PERMISSIONS_JSON%,}]"

  curl --request POST \
    --url "https://${AUTH0_DOMAIN}/api/v2/roles/${VIEWER_ROLE_ID}/permissions" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"permissions\":${PERMISSIONS_JSON}}"

  echo "Permissions assigned to viewer role."
else
  echo -e "${YELLOW}Warning: Viewer role not found.${NC}"
fi

# Analyst role gets read:analytics
ANALYST_ROLE_ID=$(curl --request GET \
  --url "https://${AUTH0_DOMAIN}/api/v2/roles" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" | jq -r ".[] | select(.name==\"analyst\") | .id")

if [ -n "$ANALYST_ROLE_ID" ] && [ "$ANALYST_ROLE_ID" != "null" ]; then
  echo "Assigning permissions to analyst role..."
  ANALYST_PERMISSIONS=("read:analytics")
  PERMISSIONS_JSON="["
  for PERMISSION in "${ANALYST_PERMISSIONS[@]}"; do
    PERMISSIONS_JSON="${PERMISSIONS_JSON}{\"permission_name\":\"${PERMISSION}\",\"resource_server_identifier\":\"${AUTH0_API_AUDIENCE}\"},"
  done
  PERMISSIONS_JSON="${PERMISSIONS_JSON%,}]"

  curl --request POST \
    --url "https://${AUTH0_DOMAIN}/api/v2/roles/${ANALYST_ROLE_ID}/permissions" \
    --header "Authorization: Bearer ${AUTH0_TOKEN}" \
    --header 'content-type: application/json' \
    --data "{\"permissions\":${PERMISSIONS_JSON}}"

  echo "Permissions assigned to analyst role."
else
  echo -e "${YELLOW}Warning: Analyst role not found.${NC}"
fi

# Configure MFA
echo "Configuring MFA..."
curl --request PATCH \
  --url "https://${AUTH0_DOMAIN}/api/v2/guardian/factors/push-notification" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" \
  --header 'content-type: application/json' \
  --data '{"enabled":true}'

curl --request PATCH \
  --url "https://${AUTH0_DOMAIN}/api/v2/guardian/factors/sms" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" \
  --header 'content-type: application/json' \
  --data '{"enabled":true}'

curl --request PATCH \
  --url "https://${AUTH0_DOMAIN}/api/v2/guardian/factors/email" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" \
  --header 'content-type: application/json' \
  --data '{"enabled":true}'

curl --request PATCH \
  --url "https://${AUTH0_DOMAIN}/api/v2/guardian/factors/otp" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" \
  --header 'content-type: application/json' \
  --data '{"enabled":true}'

# Set MFA policy for admin users
curl --request PUT \
  --url "https://${AUTH0_DOMAIN}/api/v2/guardian/policies" \
  --header "Authorization: Bearer ${AUTH0_TOKEN}" \
  --header 'content-type: application/json' \
  --data '{"policies":["all-applications"]}'

echo -e "${GREEN}Auth0 configuration completed successfully.${NC}"

# Check if OPA is running
echo -e "${GREEN}Checking if OPA is running...${NC}"
OPA_URL=${OPA_URL:-"http://opa:8181"}

if curl --output /dev/null --silent --head --fail "${OPA_URL}/health"; then
  echo "OPA is running."
else
  echo -e "${YELLOW}Warning: OPA is not running or not accessible at ${OPA_URL}.${NC}"
  echo "You can start OPA using Docker with the following command:"
  echo "docker run -p 8181:8181 openpolicyagent/opa:latest run --server"
  echo "Or deploy it to Kubernetes using the provided deployment file:"
  echo "kubectl apply -f infrastructure/kubernetes/opa-deployment.yaml"
fi

# Upload OPA policy
echo "Uploading OPA policy..."
if [ -f "infrastructure/kubernetes/opa-policies/maily-authz.rego" ]; then
  if curl --output /dev/null --silent --head --fail "${OPA_URL}/health"; then
    curl --request PUT \
      --url "${OPA_URL}/v1/policies/maily-authz" \
      --header 'content-type: text/plain' \
      --data-binary @infrastructure/kubernetes/opa-policies/maily-authz.rego

    echo "OPA policy uploaded successfully."
  else
    echo -e "${YELLOW}Warning: Could not upload OPA policy because OPA is not running.${NC}"
    echo "The policy file is available at: infrastructure/kubernetes/opa-policies/maily-authz.rego"
  fi
else
  echo -e "${YELLOW}Warning: OPA policy file not found.${NC}"
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo "You can now use Auth0 for authentication and OPA for authorization in your Maily application."
echo "Make sure to update your .env file with the correct Auth0 and OPA settings."
