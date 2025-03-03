#!/bin/bash
set -e

# Load environment variables
if [ -f .env.production ]; then
  source .env.production
else
  echo "Error: .env.production file not found"
  exit 1
fi

# Create namespace if it doesn't exist
kubectl get namespace maily-production || kubectl create namespace maily-production

# Create secret for application with dummy values for testing
kubectl create secret generic maily-secrets \
  --namespace=maily-production \
  --from-literal=openai-api-key=${OPENAI_API_KEY:-"sk-dummy-key"} \
  --from-literal=anthropic-api-key=${ANTHROPIC_API_KEY:-"sk-ant-dummy-key"} \
  --from-literal=google-ai-key=${GOOGLE_AI_API_KEY:-"dummy-key"} \
  --from-literal=mistral-api-key=${MISTRAL_API_KEY:-"dummy-key"} \
  --from-literal=groq-api-key=${GROQ_API_KEY:-"dummy-key"} \
  --from-literal=redis-password="password" \
  --from-literal=database-url="postgresql://postgres:postgres@localhost:5432/maily" \
  --from-literal=jwt-secret="dummy-secret" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets created successfully in maily-production namespace" 