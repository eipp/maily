#!/bin/bash
# setup-devops-infrastructure.sh
# Script to set up the complete DevOps infrastructure for Maily

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}Maily DevOps Infrastructure Setup${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""

# Check for required command line tools
check_commands() {
  echo -e "${GREEN}Checking for required command line tools...${NC}"
  
  local REQUIRED_COMMANDS=("aws" "kubectl" "terraform" "helm" "docker" "jq" "curl" "vercel" "vault" "git")
  local MISSING_COMMANDS=()
  
  for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
      MISSING_COMMANDS+=("$cmd")
    fi
  done
  
  if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    echo -e "${RED}The following required commands are missing:${NC}"
    for cmd in "${MISSING_COMMANDS[@]}"; do
      echo -e "${RED}- $cmd${NC}"
    done
    echo ""
    echo -e "Please install these tools before continuing."
    exit 1
  fi
  
  echo -e "${GREEN}✓ All required tools are installed${NC}"
  echo ""
}

# Configure AWS credentials
configure_aws() {
  echo -e "${GREEN}Setting up AWS credentials...${NC}"
  echo ""
  
  if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}AWS credentials not configured or invalid.${NC}"
    echo -e "Please run 'aws configure' to set up your credentials."
    
    read -p "Would you like to configure AWS credentials now? (y/n): " CONFIGURE_AWS
    if [[ "$CONFIGURE_AWS" == "y" || "$CONFIGURE_AWS" == "Y" ]]; then
      aws configure
    else
      echo -e "${YELLOW}Skipping AWS credential setup. Some functionality may be limited.${NC}"
    fi
  else
    echo -e "${GREEN}✓ AWS credentials already configured${NC}"
    aws sts get-caller-identity | jq .
  fi
  
  echo ""
}

# Set up Terraform backend
setup_terraform_backend() {
  echo -e "${GREEN}Setting up Terraform backend...${NC}"
  echo ""
  
  # Check if S3 bucket exists
  if aws s3 ls "s3://maily-terraform-state" 2>&1 | grep -q 'NoSuchBucket'; then
    echo -e "${YELLOW}Terraform state bucket does not exist. Creating...${NC}"
    
    # Create S3 bucket
    aws s3api create-bucket \
      --bucket maily-terraform-state \
      --region us-east-1
    
    # Enable versioning
    aws s3api put-bucket-versioning \
      --bucket maily-terraform-state \
      --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
      --bucket maily-terraform-state \
      --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
    
    echo -e "${GREEN}✓ Created S3 bucket for Terraform state${NC}"
  else
    echo -e "${GREEN}✓ Terraform state bucket already exists${NC}"
  fi
  
  # Check if DynamoDB table exists
  if ! aws dynamodb describe-table --table-name maily-terraform-locks &> /dev/null; then
    echo -e "${YELLOW}Terraform locks table does not exist. Creating...${NC}"
    
    # Create DynamoDB table
    aws dynamodb create-table \
      --table-name maily-terraform-locks \
      --attribute-definitions AttributeName=LockID,AttributeType=S \
      --key-schema AttributeName=LockID,KeyType=HASH \
      --billing-mode PAY_PER_REQUEST \
      --region us-east-1
    
    echo -e "${GREEN}✓ Created DynamoDB table for Terraform locks${NC}"
  else
    echo -e "${GREEN}✓ Terraform locks table already exists${NC}"
  fi
  
  echo ""
}

# Set up EKS cluster
setup_eks_cluster() {
  echo -e "${GREEN}Setting up EKS cluster...${NC}"
  echo ""
  
  # Check if EKS cluster exists
  if ! aws eks describe-cluster --name maily-production-cluster &> /dev/null; then
    echo -e "${YELLOW}EKS cluster does not exist. Creating...${NC}"
    
    # Run Terraform to create EKS cluster
    cd "$(dirname "$0")/../infrastructure/terraform"
    
    # Initialize Terraform
    terraform init
    
    # Apply Terraform configuration
    terraform apply -auto-approve
    
    echo -e "${GREEN}✓ Created EKS cluster${NC}"
    
    # Configure kubectl
    aws eks update-kubeconfig --name maily-production-cluster --region us-east-1
    
    cd - > /dev/null
  else
    echo -e "${GREEN}✓ EKS cluster already exists${NC}"
    
    # Configure kubectl
    aws eks update-kubeconfig --name maily-production-cluster --region us-east-1
  fi
  
  echo ""
}

# Set up Kubernetes namespaces
setup_kubernetes_namespaces() {
  echo -e "${GREEN}Setting up Kubernetes namespaces...${NC}"
  echo ""
  
  # Create namespaces
  kubectl apply -f "$(dirname "$0")/../kubernetes/namespaces/production.yaml"
  kubectl apply -f "$(dirname "$0")/../kubernetes/namespaces/staging.yaml"
  kubectl apply -f "$(dirname "$0")/../kubernetes/namespaces/monitoring.yaml"
  
  echo -e "${GREEN}✓ Created Kubernetes namespaces${NC}"
  echo ""
}

# Set up Vault
setup_vault() {
  echo -e "${GREEN}Setting up Vault...${NC}"
  echo ""
  
  # Check if Vault is already deployed
  if ! kubectl get deployment vault -n vault &> /dev/null; then
    echo -e "${YELLOW}Vault is not deployed. Deploying...${NC}"
    
    # Create Vault namespace
    kubectl create namespace vault --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Vault
    kubectl apply -f "$(dirname "$0")/../kubernetes/vault-deployment.yaml"
    kubectl apply -f "$(dirname "$0")/../kubernetes/vault-agent-injector.yaml"
    
    echo -e "${GREEN}✓ Deployed Vault${NC}"
    
    # Wait for Vault to be ready
    echo -e "${YELLOW}Waiting for Vault to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app=vault -n vault --timeout=300s
    
    # Initialize Vault
    echo -e "${YELLOW}Initializing Vault...${NC}"
    kubectl exec -it vault-0 -n vault -- vault operator init > vault-init.txt
    
    echo -e "${GREEN}✓ Initialized Vault${NC}"
    echo -e "${YELLOW}Vault initialization keys saved to vault-init.txt${NC}"
    echo -e "${YELLOW}IMPORTANT: Store these keys securely and delete this file!${NC}"
  else
    echo -e "${GREEN}✓ Vault is already deployed${NC}"
  fi
  
  echo ""
}

# Set up monitoring
setup_monitoring() {
  echo -e "${GREEN}Setting up monitoring...${NC}"
  echo ""
  
  # Check if Prometheus is already deployed
  if ! kubectl get deployment prometheus-server -n monitoring &> /dev/null; then
    echo -e "${YELLOW}Prometheus is not deployed. Deploying...${NC}"
    
    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Deploy Prometheus
    helm install prometheus prometheus-community/prometheus \
      --namespace monitoring \
      --set server.persistentVolume.size=20Gi \
      --set alertmanager.persistentVolume.size=5Gi
    
    echo -e "${GREEN}✓ Deployed Prometheus${NC}"
  else
    echo -e "${GREEN}✓ Prometheus is already deployed${NC}"
  fi
  
  # Check if Grafana is already deployed
  if ! kubectl get deployment grafana -n monitoring &> /dev/null; then
    echo -e "${YELLOW}Grafana is not deployed. Deploying...${NC}"
    
    # Add Grafana Helm repository
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Deploy Grafana
    helm install grafana grafana/grafana \
      --namespace monitoring \
      --set persistence.enabled=true \
      --set persistence.size=5Gi \
      --set adminPassword=admin
    
    echo -e "${GREEN}✓ Deployed Grafana${NC}"
    
    # Get Grafana admin password
    GRAFANA_PASSWORD=$(kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
    echo -e "${YELLOW}Grafana admin password: ${GRAFANA_PASSWORD}${NC}"
    echo -e "${YELLOW}IMPORTANT: Change this password after first login!${NC}"
  else
    echo -e "${GREEN}✓ Grafana is already deployed${NC}"
  fi
  
  # Check if ELK stack is already deployed
  if ! kubectl get statefulset elasticsearch-master -n monitoring &> /dev/null; then
    echo -e "${YELLOW}ELK stack is not deployed. Deploying...${NC}"
    
    # Add Elastic Helm repository
    helm repo add elastic https://helm.elastic.co
    helm repo update
    
    # Deploy Elasticsearch
    helm install elasticsearch elastic/elasticsearch \
      --namespace monitoring \
      --set replicas=1 \
      --set minimumMasterNodes=1 \
      --set resources.requests.cpu=100m \
      --set resources.requests.memory=1Gi \
      --set resources.limits.cpu=1000m \
      --set resources.limits.memory=2Gi
    
    # Deploy Kibana
    helm install kibana elastic/kibana \
      --namespace monitoring \
      --set resources.requests.cpu=100m \
      --set resources.requests.memory=500Mi \
      --set resources.limits.cpu=500m \
      --set resources.limits.memory=1Gi
    
    # Deploy Filebeat
    helm install filebeat elastic/filebeat \
      --namespace monitoring
    
    echo -e "${GREEN}✓ Deployed ELK stack${NC}"
  else
    echo -e "${GREEN}✓ ELK stack is already deployed${NC}"
  fi
  
  echo ""
}

# Set up CI/CD
setup_cicd() {
  echo -e "${GREEN}Setting up CI/CD...${NC}"
  echo ""
  
  # Check if GitHub Actions workflow file exists
  if [ ! -f "$(dirname "$0")/../.github/workflows/unified-ci-cd.yml" ]; then
    echo -e "${YELLOW}GitHub Actions workflow file does not exist. Creating...${NC}"
    
    # Create .github/workflows directory if it doesn't exist
    mkdir -p "$(dirname "$0")/../.github/workflows"
    
    # Copy the unified CI/CD workflow file
    cp "$(dirname "$0")/../.github/workflows/unified-ci-cd.yml.template" "$(dirname "$0")/../.github/workflows/unified-ci-cd.yml"
    
    echo -e "${GREEN}✓ Created GitHub Actions workflow file${NC}"
  else
    echo -e "${GREEN}✓ GitHub Actions workflow file already exists${NC}"
  fi
  
  echo ""
}

# Set up Docker registry
setup_docker_registry() {
  echo -e "${GREEN}Setting up Docker registry...${NC}"
  echo ""
  
  # Check if ECR repository exists
  if ! aws ecr describe-repositories --repository-names maily-api maily-web maily-workers maily-analytics maily-email maily-campaign &> /dev/null; then
    echo -e "${YELLOW}ECR repositories do not exist. Creating...${NC}"
    
    # Create ECR repositories
    aws ecr create-repository --repository-name maily-api
    aws ecr create-repository --repository-name maily-web
    aws ecr create-repository --repository-name maily-workers
    aws ecr create-repository --repository-name maily-analytics
    aws ecr create-repository --repository-name maily-email
    aws ecr create-repository --repository-name maily-campaign
    
    echo -e "${GREEN}✓ Created ECR repositories${NC}"
  else
    echo -e "${GREEN}✓ ECR repositories already exist${NC}"
  fi
  
  echo ""
}

# Set up Vercel
setup_vercel() {
  echo -e "${GREEN}Setting up Vercel...${NC}"
  echo ""
  
  # Check if Vercel CLI is authenticated
  if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}Vercel CLI is not authenticated. Authenticating...${NC}"
    
    # Authenticate Vercel CLI
    vercel login
    
    echo -e "${GREEN}✓ Authenticated Vercel CLI${NC}"
  else
    echo -e "${GREEN}✓ Vercel CLI is already authenticated${NC}"
  fi
  
  echo ""
}

# Set up WebSocket infrastructure
setup_websocket_infrastructure() {
  echo -e "${GREEN}Setting up WebSocket infrastructure...${NC}"
  echo ""
  
  # Deploy WebSocket service
  kubectl apply -f "$(dirname "$0")/../kubernetes/deployments/websocket-service.yaml"
  
  echo -e "${GREEN}✓ Deployed WebSocket service${NC}"
  echo ""
}

# Set up blockchain infrastructure
setup_blockchain_infrastructure() {
  echo -e "${GREEN}Setting up blockchain infrastructure...${NC}"
  echo ""
  
  # Check if blockchain service is already deployed
  if ! kubectl get deployment blockchain-service -n maily-production &> /dev/null; then
    echo -e "${YELLOW}Blockchain service is not deployed. Deploying...${NC}"
    
    # Deploy blockchain service
    kubectl apply -f "$(dirname "$0")/../kubernetes/deployments/blockchain-service.yaml"
    
    echo -e "${GREEN}✓ Deployed blockchain service${NC}"
  else
    echo -e "${GREEN}✓ Blockchain service is already deployed${NC}"
  fi
  
  echo ""
}

# Main function
main() {
  check_commands
  configure_aws
  setup_terraform_backend
  setup_eks_cluster
  setup_kubernetes_namespaces
  setup_vault
  setup_monitoring
  setup_cicd
  setup_docker_registry
  setup_vercel
  setup_websocket_infrastructure
  setup_blockchain_infrastructure
  
  echo -e "${GREEN}======================================================${NC}"
  echo -e "${GREEN}DevOps Infrastructure Setup Complete${NC}"
  echo -e "${GREEN}======================================================${NC}"
  echo ""
  echo -e "Next steps:"
  echo -e "1. Review the DevOps strategy document: devops-strategy.md"
  echo -e "2. Configure Vault with the necessary secrets"
  echo -e "3. Set up GitHub repository secrets for CI/CD"
  echo -e "4. Deploy the application using the CI/CD pipeline"
  echo ""
}

# Run the script
main
