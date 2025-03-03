#!/bin/bash

# Production Environment Setup Script
# This script helps configure the necessary infrastructure for Maily production deployment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}Maily Production Environment Setup${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""

# Check for required command line tools
check_commands() {
  echo -e "${GREEN}Checking for required command line tools...${NC}"
  
  local REQUIRED_COMMANDS=("aws" "kubectl" "terraform" "jq" "curl" "vercel")
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

# Configure Vercel
configure_vercel() {
  echo -e "${GREEN}Setting up Vercel...${NC}"
  echo ""
  
  if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}Vercel not authenticated.${NC}"
    echo -e "Please run 'vercel login' to authenticate with Vercel."
    
    read -p "Would you like to login to Vercel now? (y/n): " CONFIGURE_VERCEL
    if [[ "$CONFIGURE_VERCEL" == "y" || "$CONFIGURE_VERCEL" == "Y" ]]; then
      vercel login
    else
      echo -e "${YELLOW}Skipping Vercel authentication. Deployment to Vercel will fail.${NC}"
    fi
  else
    echo -e "${GREEN}✓ Vercel already authenticated${NC}"
    vercel whoami
  fi
  
  echo ""
}

# Create EKS cluster
create_eks_cluster() {
  echo -e "${GREEN}Setting up AWS EKS cluster...${NC}"
  echo ""
  
  # Check if EKS cluster already exists
  if aws eks describe-cluster --name maily-production-cluster &> /dev/null; then
    echo -e "${GREEN}✓ EKS cluster 'maily-production-cluster' already exists${NC}"
    echo -e "Getting cluster details..."
    aws eks describe-cluster --name maily-production-cluster | jq '.cluster.status,.cluster.endpoint'
  else
    echo -e "${YELLOW}EKS cluster 'maily-production-cluster' does not exist.${NC}"
    echo -e "Creating cluster using Terraform..."
    
    # Run Terraform to create EKS cluster
    if [ -d "infrastructure/terraform/eks" ]; then
      read -p "Would you like to create the EKS cluster now? (y/n): " CREATE_CLUSTER
      if [[ "$CREATE_CLUSTER" == "y" || "$CREATE_CLUSTER" == "Y" ]]; then
        cd infrastructure/terraform/eks
        terraform init
        terraform plan -out=tfplan
        
        echo -e "${YELLOW}Review the Terraform plan above.${NC}"
        read -p "Would you like to apply this plan? (y/n): " APPLY_PLAN
        if [[ "$APPLY_PLAN" == "y" || "$APPLY_PLAN" == "Y" ]]; then
          terraform apply tfplan
          echo -e "${GREEN}✓ EKS cluster creation initiated${NC}"
        else
          echo -e "${YELLOW}Skipping EKS cluster creation.${NC}"
        fi
        cd - > /dev/null
      else
        echo -e "${YELLOW}Skipping EKS cluster creation.${NC}"
      fi
    else
      echo -e "${RED}Terraform EKS configuration not found in infrastructure/terraform/eks${NC}"
      echo -e "Please check the repository structure."
    fi
  fi
  
  echo ""
}

# Configure kubectl
configure_kubectl() {
  echo -e "${GREEN}Configuring kubectl for EKS cluster...${NC}"
  echo ""
  
  read -p "Would you like to update kubectl config for EKS cluster? (y/n): " UPDATE_KUBECONFIG
  if [[ "$UPDATE_KUBECONFIG" == "y" || "$UPDATE_KUBECONFIG" == "Y" ]]; then
    aws eks update-kubeconfig --region us-east-1 --name maily-production-cluster
    echo -e "${GREEN}✓ kubectl configured for EKS cluster${NC}"
    
    echo -e "Testing kubectl configuration..."
    kubectl get namespaces
  else
    echo -e "${YELLOW}Skipping kubectl configuration.${NC}"
  fi
  
  echo ""
}

# Set up DNS records
configure_dns() {
  echo -e "${GREEN}Configuring DNS records...${NC}"
  echo -e "${YELLOW}Note: This typically requires access to your domain registrar or DNS provider.${NC}"
  echo ""
  
  echo -e "Required DNS Records:"
  echo -e "1. A record for 'justmaily.com' pointing to your Vercel deployment"
  echo -e "2. A record for 'api.justmaily.com' pointing to your Vercel deployment"
  echo ""
  
  read -p "Have you configured these DNS records? (y/n): " DNS_CONFIGURED
  if [[ "$DNS_CONFIGURED" == "y" || "$DNS_CONFIGURED" == "Y" ]]; then
    echo -e "${GREEN}✓ DNS records configured${NC}"
    
    echo -e "Testing DNS resolution..."
    if host justmaily.com &> /dev/null; then
      echo -e "${GREEN}✓ justmaily.com resolves successfully${NC}"
    else
      echo -e "${YELLOW}Warning: justmaily.com does not resolve. DNS may still be propagating.${NC}"
    fi
    
    if host api.justmaily.com &> /dev/null; then
      echo -e "${GREEN}✓ api.justmaily.com resolves successfully${NC}"
    else
      echo -e "${YELLOW}Warning: api.justmaily.com does not resolve. DNS may still be propagating.${NC}"
    fi
  else
    echo -e "${YELLOW}Please configure DNS records before proceeding with deployment.${NC}"
  fi
  
  echo ""
}

# Create necessary secrets
configure_secrets() {
  echo -e "${GREEN}Setting up necessary secrets...${NC}"
  echo ""
  
  if [ -f ".env.production" ]; then
    echo -e "${GREEN}✓ .env.production file exists${NC}"
  else
    echo -e "${YELLOW}.env.production file not found.${NC}"
    
    if [ -f ".env.production.template" ]; then
      read -p "Would you like to create .env.production from template? (y/n): " CREATE_ENV
      if [[ "$CREATE_ENV" == "y" || "$CREATE_ENV" == "Y" ]]; then
        cp .env.production.template .env.production
        echo -e "${GREEN}✓ Created .env.production from template${NC}"
        echo -e "${YELLOW}Warning: You need to edit .env.production to add your actual secrets!${NC}"
      else
        echo -e "${YELLOW}Skipping .env.production creation.${NC}"
      fi
    else
      echo -e "${RED}.env.production.template not found!${NC}"
      echo -e "You'll need to create .env.production manually."
    fi
  fi
  
  if [ -d "kubernetes" ]; then
    echo -e "Creating Kubernetes secrets..."
    
    read -p "Would you like to create Kubernetes secrets now? (y/n): " CREATE_K8S_SECRETS
    if [[ "$CREATE_K8S_SECRETS" == "y" || "$CREATE_K8S_SECRETS" == "Y" ]]; then
      if [ -f "scripts/create-k8s-secrets.sh" ]; then
        ./scripts/create-k8s-secrets.sh
      else
        echo -e "${RED}scripts/create-k8s-secrets.sh not found!${NC}"
      fi
    else
      echo -e "${YELLOW}Skipping Kubernetes secrets creation.${NC}"
    fi
  fi
  
  echo ""
}

# Main function
main() {
  check_commands
  configure_aws
  configure_vercel
  create_eks_cluster
  configure_kubectl
  configure_dns
  configure_secrets
  
  echo -e "${GREEN}======================================================${NC}"
  echo -e "${GREEN}Environment Setup Complete${NC}"
  echo -e "${GREEN}======================================================${NC}"
  echo ""
  echo -e "Next steps:"
  echo -e "1. Review any warnings or errors above"
  echo -e "2. Edit .env.production to set actual secret values if needed"
  echo -e "3. Run deployment with: ./mailylaunch.sh deploy --env=production"
  echo -e "4. Verify deployment with: ./mailylaunch.sh verify --env=production"
  echo ""
  echo -e "For assistance with completing the deployment, please contact:"
  echo -e "- DevOps team: devops@justmaily.com"
  echo -e "- Technical lead: tech-lead@justmaily.com"
}

# Run the script
main