#!/bin/bash
# deploy-secrets-to-aws.sh
# Script to deploy secrets from .env.production to AWS Secrets Manager using Terraform

set -e

# Check if .env.production exists
if [ ! -f .env.production ]; then
  echo "Error: .env.production file not found."
  echo "Please create it from .env.production.template and populate with actual values."
  exit 1
fi

# Create a temporary directory for Terraform files
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Create main.tf in the temporary directory
cat > $TEMP_DIR/main.tf << 'EOF'
provider "aws" {
  region = var.aws_region
}

module "secrets_manager" {
  source = "../../terraform/modules/secrets_manager"

  environment      = var.environment
  secret_names     = var.secret_names
  secret_values    = var.secret_values
  env_file_content = file(var.env_file_path)
  
  tags = {
    Project     = "Maily"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

output "secret_arns" {
  description = "List of secret ARNs"
  value       = module.secrets_manager.secret_arns
}

output "env_secret_arn" {
  description = "ARN of the .env file secret"
  value       = module.secrets_manager.env_secret_arn
}

output "json_secret_arn" {
  description = "ARN of the JSON secret"
  value       = module.secrets_manager.json_secret_arn
}

output "secret_full_names" {
  description = "List of full secret names in AWS Secrets Manager"
  value       = module.secrets_manager.secret_full_names
}
EOF

# Create variables.tf in the temporary directory
cat > $TEMP_DIR/variables.tf << 'EOF'
variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., production, staging, development)"
  type        = string
  default     = "production"
}

variable "secret_names" {
  description = "List of secret names to create"
  type        = list(string)
}

variable "secret_values" {
  description = "List of secret values corresponding to secret_names"
  type        = list(string)
  sensitive   = true
}

variable "env_file_path" {
  description = "Path to the .env file"
  type        = string
}
EOF

# Create terraform.tfvars in the temporary directory
# Parse .env.production file and create a Terraform variables file
echo "aws_region = \"us-east-1\"" > $TEMP_DIR/terraform.tfvars
echo "environment = \"production\"" >> $TEMP_DIR/terraform.tfvars
echo "env_file_path = \"../../.env.production\"" >> $TEMP_DIR/terraform.tfvars

# Create temporary arrays for secret names and values
secret_names=()
secret_values=()

# Parse .env.production and add each non-empty, non-commented line as a secret
while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip empty lines and comments
  if [[ -z "$line" || "$line" =~ ^# ]]; then
    continue
  fi
  
  # Extract key and value
  if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    
    # Remove any surrounding quotes from the value
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"
    
    # Skip if the value contains a variable reference
    if [[ "$value" == *'${'* ]]; then
      continue
    fi
    
    # Add to arrays
    secret_names+=("$key")
    secret_values+=("$value")
  fi
done < .env.production

# Write secret_names to terraform.tfvars
echo "secret_names = [" >> $TEMP_DIR/terraform.tfvars
for i in "${!secret_names[@]}"; do
  if [ $i -eq $((${#secret_names[@]} - 1)) ]; then
    echo "  \"${secret_names[$i]}\"" >> $TEMP_DIR/terraform.tfvars
  else
    echo "  \"${secret_names[$i]}\"," >> $TEMP_DIR/terraform.tfvars
  fi
done
echo "]" >> $TEMP_DIR/terraform.tfvars

# Write secret_values to terraform.tfvars
echo "secret_values = [" >> $TEMP_DIR/terraform.tfvars
for i in "${!secret_values[@]}"; do
  if [ $i -eq $((${#secret_values[@]} - 1)) ]; then
    echo "  \"${secret_values[$i]}\"" >> $TEMP_DIR/terraform.tfvars
  else
    echo "  \"${secret_values[$i]}\"," >> $TEMP_DIR/terraform.tfvars
  fi
done
echo "]" >> $TEMP_DIR/terraform.tfvars

# Initialize and apply Terraform
cd $TEMP_DIR
echo "Initializing Terraform..."
terraform init

echo "Planning Terraform deployment..."
terraform plan -out=tfplan

echo "Applying Terraform deployment..."
terraform apply tfplan

echo "Secrets successfully deployed to AWS Secrets Manager!"

# Clean up
cd -
echo "Cleaning up temporary directory..."
rm -rf $TEMP_DIR

echo "Done!"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done
