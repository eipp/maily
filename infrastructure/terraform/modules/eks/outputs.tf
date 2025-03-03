# Maily EKS Cluster Module Outputs

output "cluster_id" {
  description = "The ID of the EKS cluster"
  value       = aws_eks_cluster.this.id
}

output "cluster_arn" {
  description = "The ARN of the EKS cluster"
  value       = aws_eks_cluster.this.arn
}

output "cluster_endpoint" {
  description = "The endpoint for the Kubernetes API server"
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  description = "The base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.this.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "The security group ID attached to the EKS cluster"
  value       = aws_security_group.cluster.id
}

output "node_security_group_id" {
  description = "The security group ID attached to the EKS nodes"
  value       = aws_security_group.cluster.id
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = aws_iam_openid_connect_provider.this.arn
}

output "oidc_provider_url" {
  description = "The URL of the OIDC Provider"
  value       = aws_iam_openid_connect_provider.this.url
}

output "node_role_arn" {
  description = "The ARN of the IAM role for the EKS nodes"
  value       = aws_iam_role.node.arn
}

output "node_role_name" {
  description = "The name of the IAM role for the EKS nodes"
  value       = aws_iam_role.node.name
}

output "cluster_role_arn" {
  description = "The ARN of the IAM role for the EKS cluster"
  value       = aws_iam_role.cluster.arn
}

output "cluster_role_name" {
  description = "The name of the IAM role for the EKS cluster"
  value       = aws_iam_role.cluster.name
}

output "node_groups" {
  description = "Map of node groups created and their attributes"
  value       = aws_eks_node_group.this
}
