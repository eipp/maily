output "cluster_id" {
  description = "The name/id of the EKS cluster"
  value       = aws_eks_cluster.main.id
}

output "cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the cluster"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "The endpoint for the Kubernetes API server"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_security_group.eks_cluster_sg.id
}

output "node_security_group_id" {
  description = "Security group ID attached to the EKS nodes"
  value       = aws_security_group.eks_nodes_sg.id
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = local.cluster_name
}

output "aws_load_balancer_controller_role_arn" {
  description = "ARN of the IAM role for AWS Load Balancer Controller"
  value       = aws_iam_role.aws_load_balancer_controller.arn
}

output "cluster_autoscaler_role_arn" {
  description = "ARN of the IAM role for Cluster Autoscaler"
  value       = aws_iam_role.cluster_autoscaler.arn
}

output "external_dns_role_arn" {
  description = "ARN of the IAM role for External DNS"
  value       = aws_iam_role.external_dns.arn
}

output "node_groups" {
  description = "Map of EKS node groups"
  value = {
    for k, v in aws_eks_node_group.main : k => {
      id         = v.id
      arn        = v.arn
      status     = v.status
      node_group = v.node_group_name
    }
  }
}

output "kubeconfig" {
  description = "kubectl config that can be used to connect to the cluster"
  value = templatefile("${path.module}/templates/kubeconfig.tpl", {
    cluster_name                  = aws_eks_cluster.main.name
    cluster_endpoint              = aws_eks_cluster.main.endpoint
    cluster_certificate_authority = aws_eks_cluster.main.certificate_authority[0].data
    region                        = data.aws_region.current.name
  })
  sensitive = true
}

# Get current AWS region
data "aws_region" "current" {}
