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

# Create secret for Docker registry
kubectl create secret docker-registry registry-credentials \
  --namespace=maily-production \
  --docker-server=${DOCKER_REGISTRY_SERVER} \
  --docker-username=${DOCKER_USERNAME} \
  --docker-password=${DOCKER_PASSWORD} \
  --dry-run=client -o yaml | kubectl apply -f -

# Create secret for application
kubectl create secret generic maily-secrets \
  --namespace=maily-production \
  --from-literal=openai-api-key=${OPENAI_API_KEY} \
  --from-literal=anthropic-api-key=${ANTHROPIC_API_KEY} \
  --from-literal=google-ai-key=${GOOGLE_AI_API_KEY} \
  --from-literal=mistral-api-key=${MISTRAL_API_KEY} \
  --from-literal=groq-api-key=${GROQ_API_KEY} \
  --from-literal=redis-password=${REDIS_PASSWORD} \
  --from-literal=database-url=${POSTGRES_AI_DB_URL} \
  --from-literal=jwt-secret=${JWT_SECRET_KEY} \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets created successfully in maily-production namespace" 