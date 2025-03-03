# AWS Secrets Manager Module

This Terraform module manages secrets in AWS Secrets Manager for the Maily application.

## Features

- Creates individual secrets for each key-value pair
- Optionally creates a secret for the entire .env file
- Optionally creates a JSON secret with all values
- Configurable recovery window
- Support for custom KMS keys
- Tagging support

## Usage

```hcl
module "secrets_manager" {
  source = "./modules/secrets_manager"

  environment = "production"
  
  secrets = {
    "db/password"        = "your-db-password"
    "jwt/secret"         = "your-jwt-secret"
    "sendgrid/api_key"   = "your-sendgrid-api-key"
    "mailgun/api_key"    = "your-mailgun-api-key"
    "openai/api_key"     = "your-openai-api-key"
  }
  
  # Optional: Store the entire .env file as a secret
  create_env_secret = true
  env_file_content  = file(".env.production")
  
  # Optional: Store all secrets as a JSON object
  create_json_secret = true
  
  # Optional: Custom recovery window
  recovery_window_in_days = 7
  
  # Optional: Custom KMS key
  kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/your-kms-key-id"
  
  # Optional: Custom tags
  tags = {
    Project     = "Maily"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
```

## Automated Deployment

You can use the `scripts/deploy-secrets-to-aws.sh` script to automatically deploy secrets from your `.env.production` file to AWS Secrets Manager:

```bash
./scripts/deploy-secrets-to-aws.sh
```

This script:
1. Reads your `.env.production` file
2. Creates a temporary Terraform configuration
3. Deploys the secrets to AWS Secrets Manager
4. Cleans up the temporary files

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| secrets | Map of secret name to secret value | `map(string)` | `{}` | no |
| environment | Environment name (e.g., production, staging, development) | `string` | `"production"` | no |
| recovery_window_in_days | Number of days that AWS Secrets Manager waits before it can delete the secret | `number` | `30` | no |
| kms_key_id | ARN or Id of the AWS KMS key to be used to encrypt the secret values | `string` | `null` | no |
| tags | A map of tags to add to all resources | `map(string)` | `{}` | no |
| create_env_secret | Whether to create a secret for the entire .env file | `bool` | `true` | no |
| env_file_content | Content of the .env file to store as a secret | `string` | `""` | no |
| create_json_secret | Whether to create a JSON secret with all values | `bool` | `true` | no |

## Outputs

| Name | Description |
|------|-------------|
| secret_arns | Map of secret names to their ARNs |
| env_secret_arn | ARN of the .env file secret |
| json_secret_arn | ARN of the JSON secret |
| secret_names | Map of secret names to their Secrets Manager names |

## Security Considerations

- All secret values are marked as sensitive in Terraform
- Secrets are encrypted at rest using AWS KMS
- Recovery window prevents accidental deletion
- Use IAM policies to restrict access to secrets
