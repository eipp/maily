output "cluster_id" {
  description = "The name/id of the EKS cluster"
  value       = module.eks.cluster_id
}

output "cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the cluster"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "The endpoint for the Kubernetes API server"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "node_security_group_id" {
  description = "Security group ID attached to the EKS nodes"
  value       = module.eks.node_security_group_id
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = module.eks.oidc_provider_arn
}

output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "aws_load_balancer_controller_role_arn" {
  description = "ARN of the IAM role for AWS Load Balancer Controller"
  value       = module.eks.aws_load_balancer_controller_role_arn
}

output "cluster_autoscaler_role_arn" {
  description = "ARN of the IAM role for Cluster Autoscaler"
  value       = module.eks.cluster_autoscaler_role_arn
}

output "external_dns_role_arn" {
  description = "ARN of the IAM role for External DNS"
  value       = module.eks.external_dns_role_arn
}

output "node_groups" {
  description = "Map of EKS node groups"
  value       = module.eks.node_groups
}

output "kubeconfig_path" {
  description = "Path to the kubeconfig file"
  value       = "${path.module}/kubeconfig"
}

output "aws_region" {
  description = "AWS region where the EKS cluster is deployed"
  value       = var.aws_region
}

output "vpc_id" {
  description = "ID of the VPC where the EKS cluster is deployed"
  value       = data.aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs where the EKS cluster is deployed"
  value       = local.private_subnet_ids
}
