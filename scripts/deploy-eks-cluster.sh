#!/bin/bash
# deploy-eks-cluster.sh
# Script to deploy an EKS cluster using Terraform

set -e

# Change to the EKS directory
cd "$(dirname "$0")/../terraform/eks"

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
terraform plan -out=tfplan

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

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

