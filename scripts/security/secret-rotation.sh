#!/bin/bash
# Automated Secret Rotation Script for Vault and Kubernetes
# This script handles the rotation of secrets in Vault and updates Kubernetes with the new values

set -e

# Configuration
VAULT_ADDR=${VAULT_ADDR:-"https://vault.vault.svc.cluster.local:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-""}
KUBERNETES_NAMESPACE=${KUBERNETES_NAMESPACE:-"maily-production"}
ROTATION_LOG_FILE=${ROTATION_LOG_FILE:-"/var/log/maily/secret-rotation.log"}
ROTATION_MODE=${ROTATION_MODE:-"all"} # Options: all, database, api, redis, llm, jwt

# Log configuration
mkdir -p "$(dirname "$ROTATION_LOG_FILE")"
exec > >(tee -a "$ROTATION_LOG_FILE") 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting secret rotation: $ROTATION_MODE"

# Check if Vault token is provided
if [ -z "$VAULT_TOKEN" ]; then
    echo "Error: VAULT_TOKEN environment variable must be set"
    exit 1
fi

# Set Vault token for authentication
export VAULT_TOKEN
export VAULT_ADDR

# Function to rotate database credentials
rotate_database_credentials() {
    echo "Rotating database credentials..."
    
    # Check if database secrets engine is enabled
    vault secrets list | grep -q "^database/" || {
        echo "Database secrets engine not enabled in Vault"
        return 1
    }
    
    # Rotate credentials for each database role
    for role in api-service analytics-service campaign-service email-service; do
        echo "Rotating credentials for role: $role"
        
        # Request new credentials from Vault
        new_creds=$(vault read -format=json "database/creds/$role")
        
        if [ $? -ne 0 ]; then
            echo "Failed to rotate credentials for role: $role. Skipping."
            continue
        fi
        
        username=$(echo "$new_creds" | jq -r .data.username)
        password=$(echo "$new_creds" | jq -r .data.password)
        
        # Update Kubernetes secret
        echo "Updating Kubernetes secret for $role"
        kubectl create secret generic "db-credentials-$role" \
            --namespace "$KUBERNETES_NAMESPACE" \
            --from-literal=username="$username" \
            --from-literal=password="$password" \
            --dry-run=client -o yaml | kubectl apply -f -
            
        # Store lease ID for renewal/revocation management
        lease_id=$(echo "$new_creds" | jq -r .lease_id)
        echo "$lease_id" > "/var/run/maily/leases/$role-lease.id"
        
        echo "Successfully rotated database credentials for $role"
    done
}

# Function to rotate API keys
rotate_api_keys() {
    echo "Rotating API keys..."
    
    # Rotate API keys stored in Vault
    for api in "sendgrid" "mailgun" "twilio" "stripe" "aws"; do
        echo "Rotating $api API key"
        
        # Generate a new API key (implementation depends on the service)
        case $api in
            "sendgrid")
                # Call SendGrid API to generate new key - just a placeholder
                # In real implementation, you would call the SendGrid API here
                new_api_key=$(openssl rand -base64 32)
                ;;
            "mailgun")
                # Call Mailgun API to generate new key
                new_api_key=$(openssl rand -base64 32)
                ;;
            "twilio")
                # Call Twilio API to generate new key
                new_api_key=$(openssl rand -base64 32)
                ;;
            "stripe")
                # Call Stripe API to generate new key
                new_api_key=$(openssl rand -base64 32)
                ;;
            "aws")
                # Rotate AWS access keys
                new_api_key=$(openssl rand -base64 32)
                new_secret_key=$(openssl rand -base64 32)
                ;;
            *)
                echo "Unknown API: $api. Skipping."
                continue
                ;;
        esac
        
        # Store the new key in Vault
        if [ "$api" == "aws" ]; then
            vault kv put "secret/api/$api" \
                access_key="$new_api_key" \
                secret_key="$new_secret_key"
        else
            vault kv put "secret/api/$api" \
                api_key="$new_api_key"
        fi
        
        # Update Kubernetes secret
        echo "Updating Kubernetes secret for $api"
        if [ "$api" == "aws" ]; then
            kubectl create secret generic "$api-credentials" \
                --namespace "$KUBERNETES_NAMESPACE" \
                --from-literal=access_key="$new_api_key" \
                --from-literal=secret_key="$new_secret_key" \
                --dry-run=client -o yaml | kubectl apply -f -
        else
            kubectl create secret generic "$api-credentials" \
                --namespace "$KUBERNETES_NAMESPACE" \
                --from-literal=api_key="$new_api_key" \
                --dry-run=client -o yaml | kubectl apply -f -
        fi
        
        echo "Successfully rotated $api API key"
    done
}

# Function to rotate Redis credentials
rotate_redis_credentials() {
    echo "Rotating Redis credentials..."
    
    # Generate a new strong password
    new_password=$(openssl rand -base64 32)
    
    # Update Redis with the new password - this part depends on your Redis setup
    # For example, you might use redis-cli with the AUTH command
    # For this example, we'll just store it in Vault and update the K8s secret
    
    # Store the new password in Vault
    vault kv put "secret/redis" password="$new_password"
    
    # Update Kubernetes secret
    echo "Updating Kubernetes secret for Redis"
    kubectl create secret generic "redis-credentials" \
        --namespace "$KUBERNETES_NAMESPACE" \
        --from-literal=password="$new_password" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo "Successfully rotated Redis credentials"
    
    # Note: In a real implementation, you would need to:
    # 1. Connect to Redis and change the password
    # 2. Update all services that depend on Redis to use the new password
    # 3. This might involve restarting services or using a secret management solution
}

# Function to rotate LLM API keys
rotate_llm_api_keys() {
    echo "Rotating LLM API keys..."
    
    # For demonstration purposes, we're simulating API key rotation
    # In production, this would involve calling the respective LLM APIs
    for llm in "openai" "anthropic" "mistral" "google" "groq"; do
        echo "Rotating $llm API key"
        
        # Simulate generating a new API key
        new_api_key=$(openssl rand -base64 32)
        
        # Store the new key in Vault
        vault kv put "secret/llm/$llm" api_key="$new_api_key"
        
        # Update Kubernetes secret
        echo "Updating Kubernetes secret for $llm"
        kubectl create secret generic "llm-api-keys" \
            --namespace "$KUBERNETES_NAMESPACE" \
            --from-literal="$llm"="$new_api_key" \
            --dry-run=client -o yaml | kubectl apply -f -
        
        echo "Successfully rotated $llm API key"
    done
}

# Function to rotate JWT secrets
rotate_jwt_secrets() {
    echo "Rotating JWT signing secrets..."
    
    # Generate new JWT signing key
    new_signing_key=$(openssl rand -base64 64)
    
    # Store the new key in Vault
    vault kv put "secret/jwt" signing_key="$new_signing_key"
    
    # Update Kubernetes secret
    echo "Updating Kubernetes secret for JWT"
    kubectl create secret generic "jwt-secrets" \
        --namespace "$KUBERNETES_NAMESPACE" \
        --from-literal=signing_key="$new_signing_key" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo "Successfully rotated JWT signing secrets"
}

# Function to update services after rotation
update_services() {
    echo "Updating services to use new credentials..."
    
    # Optional: add service-specific logic to handle credential updates
    # For example, if services need to be restarted to pick up new credentials
    
    # This depends on how your services are designed to handle credential changes
    # Some options:
    # 1. Services automatically reload credentials periodically
    # 2. Services subscribe to a notification when credentials change
    # 3. Services need to be restarted
    
    # For demonstration, we'll just restart deployments that don't support dynamic reloading
    kubectl rollout restart deployment -n "$KUBERNETES_NAMESPACE" api || true
    kubectl rollout restart deployment -n "$KUBERNETES_NAMESPACE" analytics || true
    kubectl rollout restart deployment -n "$KUBERNETES_NAMESPACE" email || true
    kubectl rollout restart deployment -n "$KUBERNETES_NAMESPACE" campaign || true
    kubectl rollout restart deployment -n "$KUBERNETES_NAMESPACE" workers || true
    
    echo "Services updated successfully"
}

# Main execution flow
case $ROTATION_MODE in
    "all")
        rotate_database_credentials
        rotate_api_keys
        rotate_redis_credentials
        rotate_llm_api_keys
        rotate_jwt_secrets
        update_services
        ;;
    "database")
        rotate_database_credentials
        update_services
        ;;
    "api")
        rotate_api_keys
        update_services
        ;;
    "redis")
        rotate_redis_credentials
        update_services
        ;;
    "llm")
        rotate_llm_api_keys
        update_services
        ;;
    "jwt")
        rotate_jwt_secrets
        update_services
        ;;
    *)
        echo "Invalid rotation mode: $ROTATION_MODE"
        echo "Valid options: all, database, api, redis, llm, jwt"
        exit 1
        ;;
esac

echo "$(date '+%Y-%m-%d %H:%M:%S') - Secret rotation completed successfully"
