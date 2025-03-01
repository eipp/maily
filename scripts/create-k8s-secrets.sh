#!/bin/bash
# Script to create Kubernetes secrets from environment variables
# Run this after the EKS cluster is set up but before deploying services

set -e

NAMESPACE="maily-production"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
  echo "kubectl is not installed. Please install it first."
  exit 1
fi

# Ensure namespace exists
kubectl get namespace $NAMESPACE > /dev/null 2>&1 || kubectl create namespace $NAMESPACE

# Create secrets from environment variables
echo "Creating Kubernetes secrets from environment variables..."

# Load environment variables if not already loaded
if [ -z "$OPENAI_API_KEY" ]; then
  if [ -f ".env.production" ]; then
    echo "Loading environment variables from .env.production..."
    export $(grep -v '^#' .env.production | xargs)
  else
    echo "Error: .env.production file not found and environment variables are not set."
    exit 1
  fi
fi

# Create main secrets object
kubectl create secret generic maily-secrets \
  --namespace=$NAMESPACE \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  --from-literal=anthropic-api-key="$ANTHROPIC_API_KEY" \
  --from-literal=google-ai-key="$GOOGLE_AI_API_KEY" \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=redis-password="$REDIS_PASSWORD" \
  --from-literal=rabbitmq-password="$RABBITMQ_PASSWORD" \
  --from-literal=jwt-secret-key="$JWT_SECRET_KEY" \
  --from-literal=clerk-secret-key="$CLERK_SECRET_KEY" \
  --from-literal=resend-api-key="$RESEND_API_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

# Create dedicated Redis password secret
kubectl create secret generic redis-password \
  --namespace=$NAMESPACE \
  --from-literal=redis-password="$REDIS_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

# Create dedicated RabbitMQ credentials secret
kubectl create secret generic rabbitmq-credentials \
  --namespace=$NAMESPACE \
  --from-literal=rabbitmq-username="$RABBITMQ_USER" \
  --from-literal=rabbitmq-password="$RABBITMQ_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

# Create TLS certificates secret (if available)
if [ -n "$TLS_CERT" ] && [ -n "$TLS_KEY" ]; then
  echo "Creating TLS secret..."
  kubectl create secret tls maily-tls \
    --namespace=$NAMESPACE \
    --cert="$TLS_CERT" \
    --key="$TLS_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -
fi

echo "Kubernetes secrets created successfully in namespace $NAMESPACE."
