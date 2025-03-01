#!/bin/bash
set -e

# Configuration
BACKUP_SCRIPT="/vault/scripts/backup.sh"
ROTATION_SCRIPT="/vault/scripts/rotate-prod-secrets.sh"
ACTION="${1:-all}"  # Default to running all tasks

# Log function
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check environment
if [ -z "$VAULT_ADDR" ] || [ -z "$VAULT_TOKEN" ]; then
  log "Error: VAULT_ADDR and VAULT_TOKEN environment variables must be set"
  exit 1
fi

# Run backup
run_backup() {
  log "Starting Vault backup..."
  if [ -f "$BACKUP_SCRIPT" ]; then
    $BACKUP_SCRIPT
    log "Backup completed successfully"
  else
    log "Error: Backup script not found at $BACKUP_SCRIPT"
    exit 1
  fi
}

# Rotate secrets
rotate_secrets() {
  log "Starting secret rotation..."
  if [ -f "$ROTATION_SCRIPT" ]; then
    $ROTATION_SCRIPT
    log "Secret rotation completed successfully"
  else
    log "Error: Rotation script not found at $ROTATION_SCRIPT"
    exit 1
  fi
}

# Clean up old tokens and leases
cleanup_tokens() {
  log "Cleaning up expired tokens and leases..."

  # Get count of tokens before cleanup
  TOKEN_COUNT_BEFORE=$(vault list -format=json auth/token/accessors | jq '. | length')

  # Clean up tokens
  vault token tidy

  # Get count of tokens after cleanup
  TOKEN_COUNT_AFTER=$(vault list -format=json auth/token/accessors | jq '. | length')

  log "Token cleanup completed: Removed $(($TOKEN_COUNT_BEFORE - $TOKEN_COUNT_AFTER)) tokens"
}

# Run health check
health_check() {
  log "Running Vault health checks..."

  # Check Vault status
  HEALTH_STATUS=$(vault status -format=json)
  SEALED=$(echo $HEALTH_STATUS | jq -r '.sealed')

  if [ "$SEALED" == "true" ]; then
    log "CRITICAL: Vault is sealed and needs to be unsealed!"
    exit 1
  fi

  # Check HA status
  HA_STATUS=$(vault operator raft list-peers -format=json)
  LEADER_COUNT=$(echo $HA_STATUS | jq '.data.servers[] | select(.leader=="true") | length')

  if [ "$LEADER_COUNT" != "1" ]; then
    log "WARNING: Found $LEADER_COUNT leader(s) in the cluster. Expected exactly 1."
  fi

  log "Health check completed successfully"
}

# Main execution
log "Starting Vault maintenance tasks"

case "$ACTION" in
  "backup")
    run_backup
    ;;
  "rotate")
    rotate_secrets
    ;;
  "cleanup")
    cleanup_tokens
    ;;
  "health")
    health_check
    ;;
  "all")
    health_check
    run_backup
    rotate_secrets
    cleanup_tokens
    ;;
  *)
    log "Error: Unknown action '$ACTION'. Valid options: backup, rotate, cleanup, health, all"
    exit 1
    ;;
esac

log "Vault maintenance completed successfully"
