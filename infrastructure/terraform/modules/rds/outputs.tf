output "id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.this.id
}

output "arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.this.arn
}

output "endpoint" {
  description = "Connection endpoint of the RDS instance"
  value       = aws_db_instance.this.endpoint
}

output "address" {
  description = "Address of the RDS instance"
  value       = aws_db_instance.this.address
}

output "port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.this.port
}

output "name" {
  description = "Database name"
  value       = aws_db_instance.this.db_name
}

output "username" {
  description = "Master username"
  value       = aws_db_instance.this.username
}

output "password" {
  description = "Master password"
  value       = var.create_random_password ? random_password.master_password[0].result : var.password
  sensitive   = true
}

output "security_group_id" {
  description = "ID of the security group created for the RDS instance"
  value       = var.create_security_group ? aws_security_group.this[0].id : null
}

output "subnet_group_name" {
  description = "Name of the subnet group"
  value       = local.subnet_group_name
}

output "parameter_group_name" {
  description = "Name of the parameter group"
  value       = local.parameter_group_name
}

output "option_group_name" {
  description = "Name of the option group"
  value       = local.option_group_name
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = var.create_kms_key ? aws_kms_key.this[0].arn : var.kms_key_arn
}

output "kms_key_id" {
  description = "ID of the KMS key used for encryption"
  value       = var.create_kms_key ? aws_kms_key.this[0].key_id : null
} 