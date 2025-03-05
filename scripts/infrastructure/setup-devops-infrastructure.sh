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
  
  # First check if AWS credentials exist in the general .env file
  ENV_FILE="../.env"
  if [ -f "$ENV_FILE" ]; then
    # Source the .env file
    source "$ENV_FILE"
    
    # Check if AWS credentials are present in .env
    if [[ -n "$AWS_ACCESS_KEY_ID" && -n "$AWS_SECRET_ACCESS_KEY" ]]; then
      echo -e "${GREEN}Found AWS credentials in .env file${NC}"
      export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
      export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
      export AWS_REGION="${AWS_REGION:-us-east-1}"
      
      # Verify the credentials work
      if aws sts get-caller-identity &> /dev/null; then
        echo -e "${GREEN}✓ AWS credentials from .env are valid${NC}"
        aws sts get-caller-identity | jq .
        return 0
      fi
    fi
  fi
  
  # If we get here, either .env doesn't exist or credentials are invalid
  # Fall back to aws.env file
  AWS_ENV_TEMPLATE="../config/environments/production/aws.env.template"
  AWS_ENV_FILE="../config/environments/production/aws.env"
  
  if [ ! -f "$AWS_ENV_FILE" ] && [ -f "$AWS_ENV_TEMPLATE" ]; then
    echo -e "${YELLOW}AWS credentials file not found. Creating from template...${NC}"
    cp "$AWS_ENV_TEMPLATE" "$AWS_ENV_FILE"
    echo -e "${GREEN}Created AWS credentials file. Please update it with your credentials.${NC}"
  fi
  
  if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}AWS credentials not configured or invalid.${NC}"
    echo -e "Please run 'aws configure' to set up your credentials."
    
    read -p "Would you like to configure AWS credentials now? (y/n): " CONFIGURE_AWS
    if [[ "$CONFIGURE_AWS" == "y" || "$CONFIGURE_AWS" == "Y" ]]; then
      aws configure
      
      # Update aws.env file with configured credentials
      if [ -f "$AWS_ENV_FILE" ]; then
        AWS_ACCESS_KEY=$(aws configure get aws_access_key_id)
        AWS_SECRET_KEY=$(aws configure get aws_secret_access_key)
        AWS_REGION=$(aws configure get region)
        
        sed -i '' "s/AWS_ACCESS_KEY_ID=.*/AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY/" "$AWS_ENV_FILE"
        sed -i '' "s/AWS_SECRET_ACCESS_KEY=.*/AWS_SECRET_ACCESS_KEY=$AWS_SECRET_KEY/" "$AWS_ENV_FILE"
        sed -i '' "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" "$AWS_ENV_FILE"
        
        echo -e "${GREEN}Updated AWS credentials file with new configuration.${NC}"
      fi
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
    cd "$(dirname "$0")/../../infrastructure/terraform"
    
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
  kubectl apply -f "$(dirname "$0")/../../kubernetes/namespaces/production.yaml"
  kubectl apply -f "$(dirname "$0")/../../kubernetes/namespaces/staging.yaml"
  
  # Create monitoring namespace (may not exist as a file)
  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
  
  echo -e "${GREEN}✓ Created Kubernetes namespaces${NC}"
  echo ""
}

# Set up Vault
setup_vault() {
  echo -e "${GREEN}Setting up Vault...${NC}"
  echo ""
  
  # Check if Vault should be installed in local environment
  if [ "$SKIP_VAULT" == "true" ]; then
    echo -e "${YELLOW}Skipping Vault setup as requested by SKIP_VAULT=true${NC}"
    return 0
  fi
  
  # Create Vault namespace
  kubectl create namespace vault --dry-run=client -o yaml | kubectl apply -f -
  
  # Check for local development environment
  IS_LOCAL=false
  if kubectl config current-context | grep -q "docker-desktop\|minikube\|kind"; then
    IS_LOCAL=true
    echo -e "${YELLOW}Detected local Kubernetes cluster. Using dev mode for Vault.${NC}"
    
    # Deploy Vault in dev mode for local environments
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vault-dev
  namespace: vault
  labels:
    app: vault-dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vault-dev
  template:
    metadata:
      labels:
        app: vault-dev
    spec:
      containers:
      - name: vault
        image: hashicorp/vault:1.15.2
        command:
        - "vault"
        - "server"
        - "-dev"
        - "-dev-listen-address=0.0.0.0:8200"
        - "-dev-root-token-id=root"
        ports:
        - containerPort: 8200
          name: api
        env:
        - name: VAULT_DEV_ROOT_TOKEN_ID
          value: "root"
        - name: VAULT_DEV_LISTEN_ADDRESS
          value: "0.0.0.0:8200"
---
apiVersion: v1
kind: Service
metadata:
  name: vault
  namespace: vault
spec:
  selector:
    app: vault-dev
  ports:
  - name: http
    port: 8200
    targetPort: 8200
EOF
    
    echo -e "${GREEN}✓ Deployed Vault in dev mode for local development${NC}"
    
    # Wait for Vault to be ready
    echo -e "${YELLOW}Waiting for Vault to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app=vault-dev -n vault --timeout=300s
    
    echo -e "${GREEN}✓ Vault dev mode is ready${NC}"
    echo -e "${YELLOW}Dev mode Vault is running with root token 'root'${NC}"
    echo -e "${YELLOW}WARNING: This is for development only. Not for production use!${NC}"
  else
    # For production clusters, deploy the full setup
    # Check if Vault is already deployed
    if ! kubectl get statefulset vault -n vault &> /dev/null; then
      echo -e "${YELLOW}Vault is not deployed. Deploying...${NC}"
      
      # Deploy Vault
      kubectl apply -f "$(dirname "$0")/../../kubernetes/vault-deployment.yaml"
      kubectl apply -f "$(dirname "$0")/../../kubernetes/vault-agent-injector.yaml"
      
      echo -e "${GREEN}✓ Deployed Vault${NC}"
      
      # Wait for Vault to be ready
      echo -e "${YELLOW}Waiting for Vault to be ready...${NC}"
      kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=vault -n vault --timeout=300s
      
      # Initialize Vault
      echo -e "${YELLOW}Initializing Vault...${NC}"
      kubectl exec -it vault-0 -n vault -- vault operator init > vault-init.txt
      
      echo -e "${GREEN}✓ Initialized Vault${NC}"
      echo -e "${YELLOW}Vault initialization keys saved to vault-init.txt${NC}"
      echo -e "${YELLOW}IMPORTANT: Store these keys securely and delete this file!${NC}"
    else
      echo -e "${GREEN}✓ Vault is already deployed${NC}"
    fi
  fi
  
  echo ""
}

# Set up monitoring
setup_monitoring() {
  echo -e "${GREEN}Setting up monitoring...${NC}"
  echo ""
  
  # Check if monitoring should be skipped
  if [ "$SKIP_MONITORING" == "true" ]; then
    echo -e "${YELLOW}Skipping monitoring setup as requested by SKIP_MONITORING=true${NC}"
    return 0
  fi
  
  # Check if Prometheus is already deployed
  if ! kubectl get deployment prometheus-server -n monitoring &> /dev/null; then
    echo -e "${YELLOW}Prometheus is not deployed. Deploying...${NC}"
    
    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Deploy Prometheus
    helm install prometheus prometheus-community/prometheus \
      --namespace monitoring \
      --set server.persistentVolume.size=8Gi \
      --set alertmanager.persistentVolume.size=2Gi
    
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
      --set persistence.size=2Gi \
      --set adminPassword=admin
    
    echo -e "${GREEN}✓ Deployed Grafana${NC}"
    
    # Get Grafana admin password
    GRAFANA_PASSWORD=$(kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
    echo -e "${YELLOW}Grafana admin password: ${GRAFANA_PASSWORD}${NC}"
    echo -e "${YELLOW}IMPORTANT: Change this password after first login!${NC}"
  else
    echo -e "${GREEN}✓ Grafana is already deployed${NC}"
  fi
  
  # Skip ELK stack for now as it's resource-intensive
  echo -e "${YELLOW}Skipping ELK stack deployment to conserve resources.${NC}"
  echo -e "${YELLOW}To deploy ELK stack later, run the following commands:${NC}"
  echo -e "${YELLOW}helm repo add elastic https://helm.elastic.co${NC}"
  echo -e "${YELLOW}helm install elasticsearch elastic/elasticsearch --namespace monitoring ...${NC}"
  
  echo ""
}

# Set up CI/CD
setup_cicd() {
  echo -e "${GREEN}Setting up CI/CD...${NC}"
  echo ""
  
  # Check if CI/CD setup should be skipped
  if [ "$SKIP_CICD" == "true" ]; then
    echo -e "${YELLOW}Skipping CI/CD setup as requested by SKIP_CICD=true${NC}"
    return 0
  fi
  
  # Check for GitHub Actions workflow directory
  if [ -d "$(dirname "$0")/../../.github/workflows" ]; then
    # Check if GitHub Actions workflow file exists
    if [ ! -f "$(dirname "$0")/../../.github/workflows/unified-ci-cd.yml" ]; then
      echo -e "${YELLOW}GitHub Actions workflow file does not exist. Creating...${NC}"
      
      # Check if template exists
      if [ -f "$(dirname "$0")/../../.github/workflows/unified-ci-cd.yml.template" ]; then
        # Copy the unified CI/CD workflow file
        cp "$(dirname "$0")/../../.github/workflows/unified-ci-cd.yml.template" "$(dirname "$0")/../../.github/workflows/unified-ci-cd.yml"
        
        echo -e "${GREEN}✓ Created GitHub Actions workflow file${NC}"
      else
        echo -e "${YELLOW}CI/CD workflow template not found. Creating a basic workflow...${NC}"
        
        # Create a basic workflow file
        mkdir -p "$(dirname "$0")/../../.github/workflows"
        cat > "$(dirname "$0")/../../.github/workflows/unified-ci-cd.yml" <<EOL
name: Maily CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    - name: Install dependencies
      run: npm ci
    - name: Build
      run: npm run build
EOL
        
        echo -e "${GREEN}✓ Created basic CI/CD workflow file${NC}"
      fi
    else
      echo -e "${GREEN}✓ GitHub Actions workflow file already exists${NC}"
    fi
  else
    echo -e "${YELLOW}GitHub Actions directory not found. Creating it with a basic workflow...${NC}"
    
    # Create a basic workflow file
    mkdir -p "$(dirname "$0")/../../.github/workflows"
    cat > "$(dirname "$0")/../../.github/workflows/unified-ci-cd.yml" <<EOL
name: Maily CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    - name: Install dependencies
      run: npm ci
    - name: Build
      run: npm run build
EOL
    
    echo -e "${GREEN}✓ Created GitHub Actions directory and basic workflow file${NC}"
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
  
  # Check if Vercel setup should be skipped
  if [ "$SKIP_VERCEL" == "true" ]; then
    echo -e "${YELLOW}Skipping Vercel setup as requested by SKIP_VERCEL=true${NC}"
    return 0
  fi
  
  # Check if Vercel CLI is authenticated
  if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}Vercel CLI is not authenticated. Authenticating...${NC}"
    
    # Authenticate Vercel CLI
    read -p "Do you want to authenticate with Vercel now? (y/n): " VERCEL_LOGIN
    if [[ "$VERCEL_LOGIN" == "y" || "$VERCEL_LOGIN" == "Y" ]]; then
      vercel login
      echo -e "${GREEN}✓ Authenticated Vercel CLI${NC}"
    else
      echo -e "${YELLOW}Skipping Vercel authentication. Some functionality may be limited.${NC}"
    fi
  else
    echo -e "${GREEN}✓ Vercel CLI is already authenticated${NC}"
  fi
  
  echo ""
}

# Set up WebSocket infrastructure
setup_websocket_infrastructure() {
  echo -e "${GREEN}Setting up WebSocket infrastructure...${NC}"
  echo ""
  
  # Check if websocket service yaml exists
  if [ -f "$(dirname "$0")/../../kubernetes/deployments/websocket-service.yaml" ]; then
    # Deploy WebSocket service
    kubectl apply -f "$(dirname "$0")/../../kubernetes/deployments/websocket-service.yaml"
    echo -e "${GREEN}✓ Deployed WebSocket service${NC}"
  else
    echo -e "${YELLOW}WebSocket service deployment file not found. Skipping...${NC}"
  fi
  
  echo ""
}

# Set up blockchain infrastructure
setup_blockchain_infrastructure() {
  echo -e "${GREEN}Setting up blockchain infrastructure...${NC}"
  echo ""
  
  # Check if blockchain setup should be skipped
  if [ "$SKIP_BLOCKCHAIN" == "true" ]; then
    echo -e "${YELLOW}Skipping blockchain setup as requested by SKIP_BLOCKCHAIN=true${NC}"
    return 0
  fi
  
  # Check if the blockchain service yaml exists
  if [ -f "$(dirname "$0")/../../kubernetes/deployments/blockchain-service.yaml" ]; then
    # Clean up any previous failed deployments
    kubectl delete deployment blockchain-service -n maily --ignore-not-found
    kubectl delete service blockchain-service -n maily --ignore-not-found
    kubectl delete configmap blockchain-contracts -n maily --ignore-not-found
    kubectl delete secret blockchain-secrets -n maily --ignore-not-found
    kubectl delete serviceaccount blockchain-service -n maily --ignore-not-found
    kubectl delete role blockchain-service-role -n maily --ignore-not-found
    kubectl delete rolebinding blockchain-service-role-binding -n maily --ignore-not-found
    kubectl delete hpa blockchain-service-hpa -n maily --ignore-not-found
    
    # Create a temporary modified yaml with the variables substituted
    TEMP_BLOCKCHAIN_YAML="/tmp/blockchain-service-temp.yaml"
    DOCKER_REGISTRY="178967885703.dkr.ecr.us-east-1.amazonaws.com"
    VERSION="latest"
    
    # Create modified yaml with substituted values
    sed -e "s|\${DOCKER_REGISTRY}|$DOCKER_REGISTRY|g" \
        -e "s|\${VERSION}|$VERSION|g" \
        -e "s|namespace: maily|namespace: maily-production|g" \
        "$(dirname "$0")/../../kubernetes/deployments/blockchain-service.yaml" > "$TEMP_BLOCKCHAIN_YAML"
    
    # Check if blockchain service is already deployed in the correct namespace
    if ! kubectl get deployment blockchain-service -n maily-production &> /dev/null; then
      echo -e "${YELLOW}Blockchain service is not deployed. Deploying...${NC}"
      
      # Deploy blockchain service from the modified yaml
      kubectl apply -f "$TEMP_BLOCKCHAIN_YAML"
      
      echo -e "${GREEN}✓ Deployed blockchain service${NC}"
    else
      echo -e "${GREEN}✓ Blockchain service is already deployed${NC}"
    fi
    
    # Clean up the temporary file
    rm "$TEMP_BLOCKCHAIN_YAML"
  else
    echo -e "${YELLOW}Blockchain service deployment file not found. Skipping...${NC}"
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
