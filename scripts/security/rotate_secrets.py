#!/usr/bin/env python3
"""
Secret Rotation Script

This script provides functionality to rotate secrets in HashiCorp Vault
and update the dependent services to use the new credentials.
"""

import argparse
import base64
import os
import secrets
import subprocess
import time
from datetime import datetime
import hvac

# Constants
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "maily-dev-token")


def generate_password(length=32):
    """Generate a secure random password."""
    return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')


def get_vault_client():
    """Get an authenticated Vault client."""
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
    if not client.is_authenticated():
        raise Exception("Failed to authenticate with Vault")
    return client


def update_vault_secret(path, new_credentials):
    """Update a secret in Vault."""
    client = get_vault_client()

    # First get the current secret to retain any fields not being updated
    try:
        current_secret = client.secrets.kv.v2.read_secret_version(path=path)['data']['data']
    except Exception:
        current_secret = {}

    # Update with new credentials
    updated_secret = {**current_secret, **new_credentials}
    client.secrets.kv.v2.create_or_update_secret(
        path=path,
        secret=updated_secret
    )
    print(f"Updated secret at {path}")

    return updated_secret


def rotate_database_creds():
    """Rotate PostgreSQL credentials."""
    print("\n=== Rotating Database Credentials ===")
    new_password = generate_password()

    # Update the secret in Vault
    update_vault_secret('database', {'password': new_password})

    # Update the actual PostgreSQL password
    try:
        subprocess.run([
            'docker-compose', 'exec', '-T', 'db',
            'psql', '-U', 'postgres', '-c',
            f"ALTER USER postgres WITH PASSWORD '{new_password}';"
        ], check=True)
        print("PostgreSQL password updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update PostgreSQL password: {e}")
        return False

    return True


def rotate_redis_creds():
    """Rotate Redis credentials."""
    print("\n=== Rotating Redis Credentials ===")
    new_password = generate_password()

    # Update the secret in Vault
    update_vault_secret('redis', {'password': new_password})

    # Update the actual Redis password
    try:
        # Set the new password
        subprocess.run([
            'docker-compose', 'exec', '-T', 'redis',
            'redis-cli', 'CONFIG', 'SET', 'requirepass', new_password
        ], check=True)

        # Save the configuration
        subprocess.run([
            'docker-compose', 'exec', '-T', 'redis',
            'redis-cli', '-a', new_password, 'CONFIG', 'REWRITE'
        ], check=True)
        print("Redis password updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update Redis password: {e}")
        return False

    return True


def restart_services():
    """Restart dependent services to pick up new credentials."""
    print("\n=== Restarting Services ===")
    try:
        subprocess.run(['docker-compose', 'restart', 'api', 'workers'], check=True)
        print("Services restarted successfully")

        # Wait for services to be ready
        time.sleep(5)
        print("Checking service health...")
        health_check = subprocess.run(
            ['docker-compose', 'ps', 'api'],
            stdout=subprocess.PIPE,
            check=True
        )
        if b"healthy" in health_check.stdout:
            print("API service is healthy")
        else:
            print("Warning: API service may not be fully ready")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart services: {e}")
        return False

    return True


def backup_vault():
    """Create a backup of Vault data."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join("backups", "vault")
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = os.path.join(backup_dir, f"vault-{timestamp}.snapshot")

    print(f"\n=== Creating Vault Backup: {backup_file} ===")
    try:
        subprocess.run([
            'docker-compose', 'exec', '-T', 'vault',
            'vault', 'operator', 'raft', 'snapshot', 'save',
            '/vault/data/backup.snapshot'
        ], check=True)

        # Copy from container to host
        subprocess.run([
            'docker', 'cp',
            'maily_vault_1:/vault/data/backup.snapshot',
            backup_file
        ], check=True)

        print(f"Vault backup created at {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create Vault backup: {e}")
        return False


def main():
    """Main function to handle command line arguments and run rotations."""
    parser = argparse.ArgumentParser(description='Rotate secrets in Vault and update services')
    parser.add_argument('--database', action='store_true', help='Rotate database credentials')
    parser.add_argument('--redis', action='store_true', help='Rotate Redis credentials')
    parser.add_argument('--all', action='store_true', help='Rotate all credentials')
    parser.add_argument('--backup', action='store_true', help='Create Vault backup')
    parser.add_argument('--restart', action='store_true', help='Restart services after rotation')

    args = parser.parse_args()

    # Default to all if no specific rotation is selected
    if not (args.database or args.redis or args.all or args.backup):
        args.all = True

    # Create backup if requested
    if args.backup or args.all:
        backup_vault()

    # Rotate database credentials if requested
    if args.database or args.all:
        rotate_database_creds()

    # Rotate Redis credentials if requested
    if args.redis or args.all:
        rotate_redis_creds()

    # Restart services if requested or if rotating all credentials
    if args.restart or args.all:
        restart_services()

    print("\n=== Secret Rotation Complete ===")


if __name__ == '__main__':
    main()
