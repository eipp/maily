# AWS EKS Module

This Terraform module creates an Amazon EKS (Elastic Kubernetes Service) cluster with the following components:

- EKS Cluster with control plane logging
- EKS Node Groups for worker nodes
- IAM roles and policies for the cluster and node groups
- Security groups for the cluster and node groups
- CloudWatch Log Group for cluster logging
- IAM OIDC Provider for EKS
- IAM roles for service accounts (IRSA) for:
  - AWS Load Balancer Controller
  - Cluster Autoscaler
  - External DNS

## Usage

```hcl
module "eks" {
  source = "./modules/eks"

  project_name             = "maily"
  environment              = "production"
  vpc_id                   = "vpc-12345678"
  subnet_ids               = ["subnet-12345678", "subnet-87654321"]
  private_subnet_cidr_blocks = ["10.0.1.0/24", "10.0.2.0/24"]
  kubernetes_version       = "1.28"
  
  # Optional: Customize node groups
  node_groups = {
    general = {
      desired_size   = 2
      max_size       = 4
      min_size       = 1
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
      disk_size      = 20
      labels = {
        "role" = "general"
      }
    },
    cpu-optimized = {
      desired_size   = 2
      max_size       = 8
      min_size       = 1
      instance_types = ["c5.large"]
      capacity_type  = "SPOT"
      disk_size      = 30
      labels = {
        "role" = "cpu-optimized"
      }
    }
  }
  
  # Optional: Customize endpoint access
  endpoint_private_access = true
  endpoint_public_access  = true
  public_access_cidrs     = ["0.0.0.0/0"]
  
  # Optional: Customize logging
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  log_retention_days        = 30
  
  # Optional: Add tags
  tags = {
    Project     = "Maily"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project_name | Name of the project | `string` | `"maily"` | no |
| environment | Environment name (e.g., production, staging, development) | `string` | `"production"` | no |
| vpc_id | ID of the VPC where the EKS cluster will be created | `string` | n/a | yes |
| subnet_ids | List of subnet IDs where the EKS cluster and worker nodes will be created | `list(string)` | n/a | yes |
| private_subnet_cidr_blocks | List of private subnet CIDR blocks | `list(string)` | n/a | yes |
| kubernetes_version | Kubernetes version to use for the EKS cluster | `string` | `"1.28"` | no |
| endpoint_private_access | Whether the Amazon EKS private API server endpoint is enabled | `bool` | `true` | no |
| endpoint_public_access | Whether the Amazon EKS public API server endpoint is enabled | `bool` | `true` | no |
| public_access_cidrs | List of CIDR blocks which can access the Amazon EKS public API server endpoint | `list(string)` | `["0.0.0.0/0"]` | no |
| enabled_cluster_log_types | List of the desired control plane logging to enable | `list(string)` | `["api", "audit", "authenticator", "controllerManager", "scheduler"]` | no |
| log_retention_days | Number of days to retain log events | `number` | `30` | no |
| node_groups | Map of EKS node group configurations | `map(any)` | See variables.tf | no |
| tags | A map of tags to add to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| cluster_id | The name/id of the EKS cluster |
| cluster_arn | The Amazon Resource Name (ARN) of the cluster |
| cluster_endpoint | The endpoint for the Kubernetes API server |
| cluster_certificate_authority_data | Base64 encoded certificate data required to communicate with the cluster |
| cluster_security_group_id | Security group ID attached to the EKS cluster |
| node_security_group_id | Security group ID attached to the EKS nodes |
| oidc_provider_arn | The ARN of the OIDC Provider |
| cluster_name | The name of the EKS cluster |
| aws_load_balancer_controller_role_arn | ARN of the IAM role for AWS Load Balancer Controller |
| cluster_autoscaler_role_arn | ARN of the IAM role for Cluster Autoscaler |
| external_dns_role_arn | ARN of the IAM role for External DNS |
| node_groups | Map of EKS node groups |
| kubeconfig | kubectl config that can be used to connect to the cluster |

## Post-Deployment Steps

After deploying the EKS cluster, you'll need to:

1. Configure kubectl to connect to the cluster:
   ```bash
   aws eks update-kubeconfig --name <cluster_name> --region <region>
   ```

2. Install the AWS Load Balancer Controller:
   ```bash
   helm repo add eks https://aws.github.io/eks-charts
   helm repo update
   
   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     --namespace kube-system \
     --set clusterName=<cluster_name> \
     --set serviceAccount.create=true \
     --set serviceAccount.name=aws-load-balancer-controller \
     --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=<aws_load_balancer_controller_role_arn>
   ```

3. Install the Cluster Autoscaler:
   ```bash
   helm repo add autoscaler https://kubernetes.github.io/autoscaler
   helm repo update
   
   helm install cluster-autoscaler autoscaler/cluster-autoscaler \
     --namespace kube-system \
     --set autoDiscovery.clusterName=<cluster_name> \
     --set awsRegion=<region> \
     --set rbac.serviceAccount.create=true \
     --set rbac.serviceAccount.name=cluster-autoscaler \
     --set rbac.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=<cluster_autoscaler_role_arn>
   ```

4. Install External DNS:
   ```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
   
   helm install external-dns bitnami/external-dns \
     --namespace kube-system \
     --set provider=aws \
     --set aws.region=<region> \
     --set serviceAccount.create=true \
     --set serviceAccount.name=external-dns \
     --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=<external_dns_role_arn>
   ```

## Security Considerations

- The EKS cluster is configured with both private and public endpoint access by default
- Security groups are configured to allow only necessary traffic
- IAM roles follow the principle of least privilege
- CloudWatch logging is enabled for audit and troubleshooting
- IAM roles for service accounts (IRSA) are used to provide fine-grained permissions to Kubernetes pods
