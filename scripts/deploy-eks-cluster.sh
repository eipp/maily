#!/bin/bash
# deploy-eks-cluster.sh
# Script to deploy an EKS cluster using Terraform

set -e

# Default values
AWS_REGION="us-east-1"
CLUSTER_NAME="maily-production"
NODE_TYPE="t3.medium"
NODE_COUNT=3
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --cluster-name)
      CLUSTER_NAME="$2"
      shift 2
      ;;
    --node-type)
      NODE_TYPE="$2"
      shift 2
      ;;
    --node-count)
      NODE_COUNT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--region REGION] [--cluster-name NAME] [--node-type TYPE] [--node-count COUNT] [--dry-run]"
      exit 1
      ;;
  esac
done

# Display configuration
echo "Configuration:"
echo "  AWS Region: $AWS_REGION"
echo "  Cluster Name: $CLUSTER_NAME"
echo "  Node Type: $NODE_TYPE"
echo "  Node Count: $NODE_COUNT"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  Dry Run: Yes (no changes will be made)"
fi
echo

# Change to the infrastructure Terraform directory
cd "$(dirname "$0")/../infrastructure/terraform"

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &>/dev/null; then
  echo "Error: AWS credentials not configured or invalid."
  echo "Please configure your AWS credentials using 'aws configure' or environment variables."
  exit 1
fi

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Validate Terraform configuration
echo "Validating Terraform configuration..."
terraform validate

# Plan Terraform deployment
echo "Planning Terraform deployment..."
terraform plan \
  -var="aws_region=$AWS_REGION" \
  -var="cluster_name=$CLUSTER_NAME" \
  -var="node_instance_type=$NODE_TYPE" \
  -var="node_count=$NODE_COUNT" \
  -out=tfplan

# Ask for confirmation before applying
read -p "Do you want to apply the Terraform plan? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Deployment cancelled."
  exit 0
fi

# Apply Terraform plan
echo "Applying Terraform plan..."
terraform apply tfplan

# Get cluster information
CLUSTER_NAME=$(terraform output -raw cluster_name)
AWS_REGION=$(terraform output -raw aws_region)
KUBECONFIG_PATH=$(terraform output -raw kubeconfig_path)

echo "EKS cluster '$CLUSTER_NAME' has been successfully deployed in region '$AWS_REGION'."

# Configure kubectl
echo "Configuring kubectl..."
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION" --kubeconfig "$KUBECONFIG_PATH"

echo "Kubeconfig has been saved to: $KUBECONFIG_PATH"
echo "You can use it with: export KUBECONFIG=$KUBECONFIG_PATH"

# Get IAM role ARNs for Kubernetes add-ons
AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN=$(terraform output -raw aws_load_balancer_controller_role_arn)
CLUSTER_AUTOSCALER_ROLE_ARN=$(terraform output -raw cluster_autoscaler_role_arn)
EXTERNAL_DNS_ROLE_ARN=$(terraform output -raw external_dns_role_arn)

echo
echo "Next steps:"
echo "1. Install AWS Load Balancer Controller:"
echo "   helm repo add eks https://aws.github.io/eks-charts"
echo "   helm repo update"
echo "   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \\"
echo "     --namespace kube-system \\"
echo "     --set clusterName=$CLUSTER_NAME \\"
echo "     --set serviceAccount.create=true \\"
echo "     --set serviceAccount.name=aws-load-balancer-controller \\"
echo "     --set serviceAccount.annotations.\"eks\.amazonaws\.com/role-arn\"=$AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN"
echo
echo "2. Install Cluster Autoscaler:"
echo "   helm repo add autoscaler https://kubernetes.github.io/autoscaler"
echo "   helm repo update"
echo "   helm install cluster-autoscaler autoscaler/cluster-autoscaler \\"
echo "     --namespace kube-system \\"
echo "     --set autoDiscovery.clusterName=$CLUSTER_NAME \\"
echo "     --set awsRegion=$AWS_REGION \\"
echo "     --set rbac.serviceAccount.create=true \\"
echo "     --set rbac.serviceAccount.name=cluster-autoscaler \\"
echo "     --set rbac.serviceAccount.annotations.\"eks\.amazonaws\.com/role-arn\"=$CLUSTER_AUTOSCALER_ROLE_ARN"
echo
echo "3. Install External DNS:"
echo "   helm repo add bitnami https://charts.bitnami.com/bitnami"
echo "   helm repo update"
echo "   helm install external-dns bitnami/external-dns \\"
echo "     --namespace kube-system \\"
echo "     --set provider=aws \\"
echo "     --set aws.region=$AWS_REGION \\"
echo "     --set serviceAccount.create=true \\"
echo "     --set serviceAccount.name=external-dns \\"
echo "     --set serviceAccount.annotations.\"eks\.amazonaws\.com/role-arn\"=$EXTERNAL_DNS_ROLE_ARN"
echo
echo "EKS cluster deployment completed successfully!"

# If in dry-run mode, don't proceed with actual deployment
if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run completed. No changes were made."
  exit 0
fi

