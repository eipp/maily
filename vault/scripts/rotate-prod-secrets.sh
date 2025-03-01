#!/bin/bash
set -e

# Log file
LOG_FILE="/vault/logs/rotation-$(date +%Y%m%d).log"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Rotate database credentials
rotate_db_credentials() {
  log "Rotating database credentials..."

  # Rotate root password for PostgreSQL
  NEW_PASSWORD=$(openssl rand -base64 32)

  # Update the password in Vault
  vault write database/config/postgres \
    password="$NEW_PASSWORD"

  log "Database root credentials rotated successfully"

  # Revoke all database leases, forcing clients to get new credentials
  vault lease revoke -prefix database/
  log "All database leases revoked, clients will obtain new credentials"
}

# Rotate Redis password
rotate_redis_password() {
  log "Rotating Redis password..."

  # Generate new password
  NEW_REDIS_PASSWORD=$(openssl rand -base64 24)

  # Update Redis password in Vault
  vault kv put secret/redis \
    password="$NEW_REDIS_PASSWORD"

  # Reconfigure Redis with new password (Example - modify as needed)
  # REDIS_HOST=$(vault kv get -field=host secret/redis)
  # redis-cli -h "$REDIS_HOST" -a "$CURRENT_PASSWORD" CONFIG SET requirepass "$NEW_REDIS_PASSWORD"

  log "Redis password rotated successfully"
}

# Rotate encryption keys
rotate_encryption_keys() {
  log "Rotating encryption keys..."

  # Create new encryption key in transit engine
  NEW_KEY_NAME="maily-data-$(date +%Y%m%d)"
  vault write -f transit/keys/"$NEW_KEY_NAME"

  # Update the application config to use the new key
  vault kv put secret/application \
    encryption_key_name="$NEW_KEY_NAME"

  log "Encryption key rotated successfully"
}

# Main rotation process
log "Starting secret rotation process"
rotate_db_credentials
rotate_redis_password
rotate_encryption_keys
log "Secret rotation completed successfully"
