#!/bin/bash
set -e

# Initialize Vault
echo "Initializing Vault..."
INIT_RESPONSE=$(vault operator init -format=json -key-shares=5 -key-threshold=3)

# Parse the initialization response to get the unseal keys and root token
UNSEAL_KEYS=$(echo "$INIT_RESPONSE" | jq -r '.unseal_keys_b64[]')
ROOT_TOKEN=$(echo "$INIT_RESPONSE" | jq -r '.root_token')

# Securely store the unseal keys and root token
echo "Storing unseal keys and root token securely..."
echo "$INIT_RESPONSE" | jq > /vault/data/init-keys.json
chmod 0600 /vault/data/init-keys.json

# Unseal Vault
echo "Unsealing Vault..."
for key in $(echo "$UNSEAL_KEYS" | head -n 3); do
  vault operator unseal "$key"
done

# Log in to Vault
echo "Logging into Vault..."
vault login "$ROOT_TOKEN"

# Enable audit logging
echo "Enabling audit logging..."
vault audit enable file file_path=/vault/logs/audit.log

# Enable secrets engines
echo "Enabling secrets engines..."
vault secrets enable -path=secret kv-v2
vault secrets enable database
vault secrets enable transit

# Configure the database secrets engine for PostgreSQL
# Example - uncomment and modify as needed:
# vault write database/config/postgres \
#   plugin_name=postgresql-database-plugin \
#   allowed_roles="api-service" \
#   connection_url="postgresql://{{username}}:{{password}}@postgres:5432/maily?sslmode=disable" \
#   username="postgres" \
#   password="super-secure-password"

# Create dynamic database credentials role
# vault write database/roles/api-service \
#   db_name=postgres \
#   creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
#   default_ttl="1h" \
#   max_ttl="24h"

# Enable authentication methods
echo "Enabling authentication methods..."
vault auth enable approle
# For Kubernetes integration
# vault auth enable kubernetes

# Create policies
echo "Creating policies..."
vault policy write api-service /vault/policies/app-policy.hcl
vault policy write monitoring /vault/policies/monitoring-policy.hcl

# Create AppRole and get credentials for the API service
echo "Creating AppRole for API service..."
vault write auth/approle/role/api-service \
  secret_id_ttl=0 \
  token_num_uses=0 \
  token_ttl=20m \
  token_max_ttl=30m \
  secret_id_num_uses=0 \
  token_policies=api-service

# Get AppRole credentials
ROLE_ID=$(vault read -field=role_id auth/approle/role/api-service/role-id)
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/api-service/secret-id)

# Store these securely for the application to use
echo "AppRole Role ID: $ROLE_ID"
echo "AppRole Secret ID: $SECRET_ID"

echo "Vault initialization completed successfully!"
