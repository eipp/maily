#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups/vault"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="vault_backup_$DATE.snap"
ENCRYPTED_BACKUP="vault_backup_$DATE.snap.enc"
S3_BUCKET="maily-backups"  # Replace with your actual S3 bucket
GPG_RECIPIENT="vault-backup@maily.com"  # Replace with your GPG key identifier

# Make sure backup directory exists
mkdir -p "$BACKUP_DIR"

# Take a Vault snapshot
echo "Taking Vault snapshot..."
vault operator raft snapshot save "$BACKUP_DIR/$BACKUP_FILE"

# Encrypt the backup
echo "Encrypting the backup..."
gpg --encrypt --recipient "$GPG_RECIPIENT" --output "$BACKUP_DIR/$ENCRYPTED_BACKUP" "$BACKUP_DIR/$BACKUP_FILE"

# Remove the unencrypted backup
rm "$BACKUP_DIR/$BACKUP_FILE"

# Upload to S3 (uncomment when S3 bucket is configured)
echo "Uploading encrypted backup to S3..."
# aws s3 cp "$BACKUP_DIR/$ENCRYPTED_BACKUP" "s3://$S3_BUCKET/vault-backups/"

echo "Backup completed successfully: $BACKUP_DIR/$ENCRYPTED_BACKUP"

# Clean up old backups (keep last 7 days)
find "$BACKUP_DIR" -name "vault_backup_*.snap.enc" -type f -mtime +7 -delete
