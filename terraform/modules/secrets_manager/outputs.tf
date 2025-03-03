output "secret_arns" {
  description = "List of secret ARNs"
  value       = aws_secretsmanager_secret.maily_secrets[*].arn
}

output "env_secret_arn" {
  description = "ARN of the .env file secret"
  value       = var.create_env_secret ? aws_secretsmanager_secret.maily_env[0].arn : null
}

output "json_secret_arn" {
  description = "ARN of the JSON secret"
  value       = var.create_json_secret ? aws_secretsmanager_secret.maily_json[0].arn : null
}

output "secret_names_map" {
  description = "Map of secret names to their Secrets Manager names"
  value = {
    for i, name in var.secret_names : name => aws_secretsmanager_secret.maily_secrets[i].name
  }
}

output "secret_full_names" {
  description = "List of full secret names in AWS Secrets Manager"
  value       = aws_secretsmanager_secret.maily_secrets[*].name
}
