#!/bin/bash
set -e

# Configuration
DEV_VAULT_ADDR=${DEV_VAULT_ADDR:-"http://localhost:8200"}
DEV_VAULT_TOKEN=${DEV_VAULT_TOKEN:-"maily-dev-token"}
PROD_VAULT_ADDR=${PROD_VAULT_ADDR:-"https://localhost:8200"}
PROD_VAULT_TOKEN=${PROD_VAULT_TOKEN:-""}  # This must be provided

# Validate inputs
if [ -z "$PROD_VAULT_TOKEN" ]; then
  echo "Error: PROD_VAULT_TOKEN environment variable must be set"
  exit 1
fi

# Set up Vault CLI environment for source (dev)
export VAULT_ADDR="$DEV_VAULT_ADDR"
export VAULT_TOKEN="$DEV_VAULT_TOKEN"
export VAULT_FORMAT="json"
export VAULT_SKIP_VERIFY="true"  # Only for dev environments

# Function to log messages
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to export KV secrets from dev and import to prod
migrate_kv_secrets() {
  log "Migrating KV secrets..."

  # Get list of paths in the KV store
  PATHS=$(vault kv list -format=json secret/ | jq -r '.[]')

  # Iterate through each path
  for path in $PATHS; do
    log "Exporting secret/data/$path"

    # Get the secret data
    SECRET_DATA=$(vault kv get -format=json "secret/data/$path")

    # Switch to prod Vault
    export VAULT_ADDR="$PROD_VAULT_ADDR"
    export VAULT_TOKEN="$PROD_VAULT_TOKEN"

    # Create the secret in prod
    log "Importing secret/data/$path to production"
    echo "$SECRET_DATA" | jq -r '.data.data' | vault kv put "secret/$path" -

    # Switch back to dev Vault
    export VAULT_ADDR="$DEV_VAULT_ADDR"
    export VAULT_TOKEN="$DEV_VAULT_TOKEN"
  done

  log "KV secrets migration completed"
}

# Function to migrate policies
migrate_policies() {
  log "Migrating policies..."

  # Get list of policies (excluding default ones)
  POLICIES=$(vault policy list -format=json | jq -r '.[]' | grep -v "^default$\|^root$")

  # Iterate through each policy
  for policy in $POLICIES; do
    log "Exporting policy: $policy"

    # Get the policy data
    POLICY_DATA=$(vault policy read "$policy")

    # Switch to prod Vault
    export VAULT_ADDR="$PROD_VAULT_ADDR"
    export VAULT_TOKEN="$PROD_VAULT_TOKEN"

    # Create the policy in prod
    log "Importing policy: $policy to production"
    echo "$POLICY_DATA" | vault policy write "$policy" -

    # Switch back to dev Vault
    export VAULT_ADDR="$DEV_VAULT_ADDR"
    export VAULT_TOKEN="$DEV_VAULT_TOKEN"
  done

  log "Policy migration completed"
}

# Main migration process
log "Starting migration from dev to production Vault"
log "Source: $DEV_VAULT_ADDR"
log "Destination: $PROD_VAULT_ADDR"

# Check connectivity to dev Vault
log "Checking connection to dev Vault..."
if ! vault status > /dev/null; then
  log "Error: Could not connect to dev Vault at $DEV_VAULT_ADDR"
  exit 1
fi

# Check connectivity to prod Vault
export VAULT_ADDR="$PROD_VAULT_ADDR"
export VAULT_TOKEN="$PROD_VAULT_TOKEN"
log "Checking connection to production Vault..."
if ! vault status > /dev/null; then
  log "Error: Could not connect to production Vault at $PROD_VAULT_ADDR"
  exit 1
fi

# Reset back to dev Vault
export VAULT_ADDR="$DEV_VAULT_ADDR"
export VAULT_TOKEN="$DEV_VAULT_TOKEN"

# Perform migration
migrate_kv_secrets
migrate_policies

log "Migration completed successfully!"
log "Remember to update your application configurations to point to the production Vault."
