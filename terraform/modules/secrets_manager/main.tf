/**
 * # AWS Secrets Manager Module
 *
 * This module manages secrets in AWS Secrets Manager for the Maily application.
 * It creates and manages secrets for various components of the application.
 */

locals {
  # Use a non-sensitive list of secret names to avoid the for_each with sensitive values issue
  secret_names = var.secret_names
}

resource "aws_secretsmanager_secret" "maily_secrets" {
  count = length(local.secret_names)

  name                    = "maily/${local.secret_names[count.index]}"
  description             = "Secret for Maily: ${local.secret_names[count.index]}"
  recovery_window_in_days = var.recovery_window_in_days
  kms_key_id              = var.kms_key_id

  tags = merge(
    var.tags,
    {
      Name        = "maily/${local.secret_names[count.index]}"
      Environment = var.environment
      Service     = "maily"
    }
  )
}

resource "aws_secretsmanager_secret_version" "maily_secret_versions" {
  count = length(local.secret_names)

  secret_id     = aws_secretsmanager_secret.maily_secrets[count.index].id
  secret_string = var.secret_values[count.index]
}

# Create a secret for the entire .env file
resource "aws_secretsmanager_secret" "maily_env" {
  count = var.create_env_secret ? 1 : 0

  name                    = "maily/env/${var.environment}"
  description             = "Complete environment configuration for Maily ${var.environment}"
  recovery_window_in_days = var.recovery_window_in_days
  kms_key_id              = var.kms_key_id

  tags = merge(
    var.tags,
    {
      Name        = "maily/env/${var.environment}"
      Environment = var.environment
      Service     = "maily"
    }
  )
}

resource "aws_secretsmanager_secret_version" "maily_env_version" {
  count = var.create_env_secret ? 1 : 0

  secret_id     = aws_secretsmanager_secret.maily_env[0].id
  secret_string = var.env_file_content
}

# Create a JSON secret with all values
resource "aws_secretsmanager_secret" "maily_json" {
  count = var.create_json_secret ? 1 : 0

  name                    = "maily/json/${var.environment}"
  description             = "JSON configuration for Maily ${var.environment}"
  recovery_window_in_days = var.recovery_window_in_days
  kms_key_id              = var.kms_key_id

  tags = merge(
    var.tags,
    {
      Name        = "maily/json/${var.environment}"
      Environment = var.environment
      Service     = "maily"
    }
  )
}

resource "aws_secretsmanager_secret_version" "maily_json_version" {
  count = var.create_json_secret ? 1 : 0

  secret_id = aws_secretsmanager_secret.maily_json[0].id
  secret_string = jsonencode(
    zipmap(var.secret_names, var.secret_values)
  )
}
