output "id" {
  description = "ID of the Redis replication group"
  value       = aws_elasticache_replication_group.this.id
}

output "arn" {
  description = "ARN of the Redis replication group"
  value       = aws_elasticache_replication_group.this.arn
}

output "primary_endpoint_address" {
  description = "Address of the endpoint for the primary node"
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Address of the endpoint for the reader node(s)"
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "member_clusters" {
  description = "List of node IDs that are part of the cluster"
  value       = aws_elasticache_replication_group.this.member_clusters
}

output "port" {
  description = "Port number on which the Redis nodes accept connections"
  value       = aws_elasticache_replication_group.this.port
}

output "security_group_id" {
  description = "ID of the security group created for the Redis cluster"
  value       = var.create_security_group ? aws_security_group.this[0].id : null
}

output "parameter_group_name" {
  description = "Name of the parameter group"
  value       = local.parameter_group_name
}

output "subnet_group_name" {
  description = "Name of the subnet group"
  value       = local.subnet_group_name
}

output "kms_key_id" {
  description = "ID of the KMS key used for encryption"
  value       = var.create_kms_key ? aws_kms_key.this[0].id : var.kms_key_id
}

output "auth_token" {
  description = "Auth token for Redis authentication"
  value       = var.auth_token
  sensitive   = true
} 