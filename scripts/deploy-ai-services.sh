#!/bin/bash
# Maily AI Services Deployment Script
# This script configures and deploys the AI components of the Maily platform
# Usage: ./deploy-ai-services.sh [environment]

set -e

# Check if environment argument is provided
if [ -z "$1" ]; then
  echo "Error: No environment specified"
  echo "Usage: ./deploy-ai-services.sh [environment]"
  echo "Example: ./deploy-ai-services.sh production"
  exit 1
fi

ENVIRONMENT="$1"
LOG_FILE="deployment_logs/ai_services_${ENVIRONMENT}_$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Deploying AI services for ${ENVIRONMENT} environment..."
mkdir -p deployment_logs

# Function to display step information
step() {
  echo -e "${BLUE}-> $1${NC}" | tee -a $LOG_FILE
}

# Function to display success messages
success() {
  echo -e "${GREEN}✓ $1${NC}" | tee -a $LOG_FILE
}

# Function to display warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}" | tee -a $LOG_FILE
}

# Function to display error messages and exit
error() {
  echo -e "${RED}ERROR: $1${NC}" | tee -a $LOG_FILE
  exit 1
}

# Function to run a command with logging
run_command() {
  local cmd="$1"
  local error_msg="${2:-Command failed}"

  echo "$ $cmd" | tee -a $LOG_FILE
  if eval "$cmd" >> $LOG_FILE 2>&1; then
    return 0
  else
    local exit_code=$?
    error "${error_msg} (Exit code: ${exit_code})"
    return $exit_code
  fi
}

# Check required environment variables
step "Checking AI model credentials"
if [ -z "$OPENAI_API_KEY" ]; then
  error "OPENAI_API_KEY is not set"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  error "ANTHROPIC_API_KEY is not set"
fi

if [ -z "$GOOGLE_AI_API_KEY" ]; then
  error "GOOGLE_AI_API_KEY is not set"
fi
success "AI model credentials verified"

# Deploy AI adapters configuration
step "Configuring AI model adapters"

# Create AI adapters configuration file
AI_ADAPTERS_CONFIG="apps/api/ai/adapters/config.json"
cat > $AI_ADAPTERS_CONFIG << EOL
{
  "openai": {
    "api_key": "${OPENAI_API_KEY}",
    "models": {
      "default": "gpt-4o",
      "fast": "gpt-3.5-turbo",
      "embedding": "text-embedding-3-large"
    },
    "options": {
      "max_tokens": 4000,
      "temperature": 0.7
    }
  },
  "anthropic": {
    "api_key": "${ANTHROPIC_API_KEY}",
    "models": {
      "default": "claude-3-sonnet-20240229",
      "fast": "claude-instant-1.2",
      "premium": "claude-3-opus-20240229"
    },
    "options": {
      "max_tokens": 4000,
      "temperature": 0.7
    }
  },
  "google": {
    "api_key": "${GOOGLE_AI_API_KEY}",
    "models": {
      "default": "gemini-pro",
      "vision": "gemini-pro-vision"
    },
    "options": {
      "max_tokens": 2048,
      "temperature": 0.7
    }
  }
}
EOL
success "AI adapters configuration created"

# Deploy AI agents
step "Deploying AI agents and OctoTools framework"

# Setup OctoTools agent configuration
OCTOTOOLS_CONFIG="apps/api/ai/agents/octotools-config.json"
cat > $OCTOTOOLS_CONFIG << EOL
{
  "agents": {
    "email_composer": {
      "model": "gpt-4o",
      "provider": "openai",
      "system_prompt": "You are an expert email composer who creates high-quality, engaging emails.",
      "max_iterations": 5
    },
    "content_analyzer": {
      "model": "claude-3-sonnet-20240229",
      "provider": "anthropic",
      "system_prompt": "You are an expert content analyzer who helps identify key topics and sentiment in text.",
      "max_iterations": 3
    },
    "trust_verifier": {
      "model": "gpt-4o",
      "provider": "openai",
      "system_prompt": "You are a trust verification agent who validates email authenticity and blockchain verification.",
      "max_iterations": 2
    },
    "conversation_manager": {
      "model": "gemini-pro",
      "provider": "google",
      "system_prompt": "You are a conversation manager who helps maintain context and coherence in email threads.",
      "max_iterations": 3
    }
  },
  "workflows": {
    "email_creation": {
      "steps": [
        {"agent": "content_analyzer", "output": "content_analysis"},
        {"agent": "email_composer", "input": "content_analysis", "output": "email_draft"},
        {"agent": "trust_verifier", "input": "email_draft", "output": "verified_email"}
      ]
    },
    "email_response": {
      "steps": [
        {"agent": "conversation_manager", "output": "conversation_context"},
        {"agent": "content_analyzer", "input": "conversation_context", "output": "response_analysis"},
        {"agent": "email_composer", "input": "response_analysis", "output": "email_draft"},
        {"agent": "trust_verifier", "input": "email_draft", "output": "verified_response"}
      ]
    }
  }
}
EOL
success "OctoTools agent configuration created"

# Deploy vector database configuration
step "Configuring vector database"

if [ "$ENVIRONMENT" = "production" ]; then
  # For production, we'll use a dedicated vector database instance
  VESPA_CONFIG="apps/api/ai/vector/vespa-config.json"
  cat > $VESPA_CONFIG << EOL
{
  "endpoint": "https://vector-db.maily.io:4443",
  "cert_path": "/etc/maily/certs/vespa-client.pem",
  "key_path": "/etc/maily/certs/vespa-client-key.pem",
  "ca_path": "/etc/maily/certs/vespa-ca.pem",
  "namespace": "maily",
  "collection": "email_embeddings"
}
EOL
  success "Vector database configuration created for production"
else
  # For non-production environments, use a shared instance
  VESPA_CONFIG="apps/api/ai/vector/vespa-config.json"
  cat > $VESPA_CONFIG << EOL
{
  "endpoint": "https://vector-db-${ENVIRONMENT}.maily.io:4443",
  "cert_path": "/etc/maily/certs/vespa-client-${ENVIRONMENT}.pem",
  "key_path": "/etc/maily/certs/vespa-client-key-${ENVIRONMENT}.pem",
  "ca_path": "/etc/maily/certs/vespa-ca-${ENVIRONMENT}.pem",
  "namespace": "maily_${ENVIRONMENT}",
  "collection": "email_embeddings"
}
EOL
  success "Vector database configuration created for ${ENVIRONMENT}"
fi

# For Kubernetes-based deployment
if [ "$ENVIRONMENT" = "production" ]; then
  step "Deploying AI components to Kubernetes"

  # Update the AI service deployment in Kubernetes
  run_command "kubectl apply -f kubernetes/deployments/ai-service.yaml -n maily-${ENVIRONMENT}" "AI service deployment failed"

  # Wait for the deployment to be ready
  run_command "kubectl rollout status deployment/maily-ai-service -n maily-${ENVIRONMENT}" "AI service rollout failed"

  success "AI service deployed to Kubernetes"
else
  step "Skipping Kubernetes deployment for non-production environment"
fi

# Configure trust agents for blockchain verification
step "Configuring trust agents for blockchain verification"

TRUST_CONFIG="apps/api/ai/trust/trust-config.json"
cat > $TRUST_CONFIG << EOL
{
  "ethereum": {
    "rpc_url": "${ETHEREUM_RPC_URL}",
    "contract_address": "0x1234567890123456789012345678901234567890",
    "chain_id": 1
  },
  "polygon": {
    "rpc_url": "${POLYGON_RPC_URL}",
    "contract_address": "0x0987654321098765432109876543210987654321",
    "chain_id": 137
  },
  "verification_methods": {
    "hash_verification": true,
    "signature_verification": true,
    "timestamp_verification": true
  }
}
EOL
success "Trust agent configuration created"

# Configure AI monitoring
step "Setting up AI monitoring and telemetry"

MONITORING_CONFIG="apps/api/ai/monitoring/config.json"
cat > $MONITORING_CONFIG << EOL
{
  "metrics": {
    "latency": true,
    "tokens_used": true,
    "cost": true,
    "success_rate": true
  },
  "logging": {
    "level": "info",
    "request_logging": true,
    "response_logging": false
  },
  "alerts": {
    "error_threshold": 0.05,
    "latency_threshold_ms": 2000,
    "cost_threshold_daily": 100
  }
}
EOL
success "AI monitoring configuration created"

echo -e "\n${GREEN}=======================${NC}"
echo -e "${GREEN}AI Services Deployment Complete${NC}"
echo -e "${GREEN}=======================${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: $(date)"
echo "Log file: ${LOG_FILE}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Verify AI services are running correctly"
echo "2. Test each AI agent with sample inputs"
echo "3. Monitor usage and performance"
echo -e "${GREEN}=======================${NC}"

exit 0
