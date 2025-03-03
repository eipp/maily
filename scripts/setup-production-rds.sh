#!/bin/bash
# setup-production-rds.sh
# Script to set up production RDS database for Maily

set -e

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
  echo "Error: AWS CLI is not installed. Please install it first."
  exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &>/dev/null; then
  echo "Error: AWS credentials not configured or invalid."
  echo "Please configure your AWS credentials using 'aws configure' or environment variables."
  exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
  echo "Error: Terraform is not installed. Please install it first."
  exit 1
fi

# Default values
AWS_REGION="us-east-1"
DB_INSTANCE_CLASS="db.t3.medium"
DB_ALLOCATED_STORAGE=20
DB_MAX_ALLOCATED_STORAGE=100
DB_NAME="maily"
DB_USERNAME="maily_admin"
ENVIRONMENT="production"
PROJECT_NAME="maily"
BACKUP_RETENTION_PERIOD=7
MULTI_AZ=true
DELETION_PROTECTION=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --db-instance-class)
      DB_INSTANCE_CLASS="$2"
      shift 2
      ;;
    --db-allocated-storage)
      DB_ALLOCATED_STORAGE="$2"
      shift 2
      ;;
    --db-max-allocated-storage)
      DB_MAX_ALLOCATED_STORAGE="$2"
      shift 2
      ;;
    --db-name)
      DB_NAME="$2"
      shift 2
      ;;
    --db-username)
      DB_USERNAME="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --project-name)
      PROJECT_NAME="$2"
      shift 2
      ;;
    --backup-retention-period)
      BACKUP_RETENTION_PERIOD="$2"
      shift 2
      ;;
    --multi-az)
      MULTI_AZ="$2"
      shift 2
      ;;
    --deletion-protection)
      DELETION_PROTECTION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create a temporary directory for Terraform files
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Create main.tf in the temporary directory
cat > $TEMP_DIR/main.tf << EOF
provider "aws" {
  region = "${AWS_REGION}"
}

data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["${PROJECT_NAME}-${ENVIRONMENT}-vpc"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["${PROJECT_NAME}-${ENVIRONMENT}-private-*"]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${PROJECT_NAME}-${ENVIRONMENT}-db-subnet-group"
  subnet_ids = data.aws_subnets.private.ids

  tags = {
    Name        = "${PROJECT_NAME}-${ENVIRONMENT}-db-subnet-group"
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "aws_security_group" "db" {
  name        = "${PROJECT_NAME}-${ENVIRONMENT}-db-sg"
  description = "Security group for ${PROJECT_NAME} ${ENVIRONMENT} RDS instance"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "Allow PostgreSQL traffic from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${PROJECT_NAME}-${ENVIRONMENT}-db-sg"
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${PROJECT_NAME}/${ENVIRONMENT}/db-credentials"
  description = "Database credentials for ${PROJECT_NAME} ${ENVIRONMENT}"
  
  tags = {
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "${DB_USERNAME}"
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.main.address
    port     = 5432
    dbname   = "${DB_NAME}"
    dbInstanceIdentifier = aws_db_instance.main.id
  })
}

resource "aws_db_parameter_group" "main" {
  name   = "${PROJECT_NAME}-${ENVIRONMENT}-pg12"
  family = "postgres12"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "aws_db_instance" "main" {
  identifier             = "${PROJECT_NAME}-${ENVIRONMENT}"
  engine                 = "postgres"
  engine_version         = "12.9"
  instance_class         = "${DB_INSTANCE_CLASS}"
  allocated_storage      = ${DB_ALLOCATED_STORAGE}
  max_allocated_storage  = ${DB_MAX_ALLOCATED_STORAGE}
  storage_type           = "gp2"
  storage_encrypted      = true
  db_name                = "${DB_NAME}"
  username               = "${DB_USERNAME}"
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  parameter_group_name   = aws_db_parameter_group.main.name
  publicly_accessible    = false
  skip_final_snapshot    = false
  final_snapshot_identifier = "${PROJECT_NAME}-${ENVIRONMENT}-final-snapshot"
  backup_retention_period = ${BACKUP_RETENTION_PERIOD}
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:30-sun:05:30"
  multi_az               = ${MULTI_AZ}
  deletion_protection    = ${DELETION_PROTECTION}
  auto_minor_version_upgrade = true
  copy_tags_to_snapshot  = true
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  tags = {
    Name        = "${PROJECT_NAME}-${ENVIRONMENT}"
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

output "db_instance_address" {
  description = "The address of the RDS instance"
  value       = aws_db_instance.main.address
}

output "db_instance_endpoint" {
  description = "The connection endpoint of the RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_id" {
  description = "The RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_instance_status" {
  description = "The RDS instance status"
  value       = aws_db_instance.main.status
}

output "db_instance_name" {
  description = "The database name"
  value       = aws_db_instance.main.db_name
}

output "db_instance_username" {
  description = "The master username for the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "db_instance_port" {
  description = "The database port"
  value       = aws_db_instance.main.port
}

output "db_subnet_group_id" {
  description = "The db subnet group name"
  value       = aws_db_subnet_group.main.id
}

output "db_parameter_group_id" {
  description = "The db parameter group name"
  value       = aws_db_parameter_group.main.id
}

output "db_instance_resource_id" {
  description = "The RDS Resource ID of this instance"
  value       = aws_db_instance.main.resource_id
}

output "db_credentials_secret_arn" {
  description = "The ARN of the Secrets Manager secret storing the DB credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}
EOF

# Initialize and apply Terraform
cd $TEMP_DIR
echo "Initializing Terraform..."
terraform init

echo "Planning Terraform deployment..."
terraform plan -out=tfplan

# Ask for confirmation before applying
read -p "Do you want to apply the Terraform plan and create the RDS instance? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "RDS setup cancelled."
  exit 0
fi

echo "Applying Terraform plan..."
terraform apply tfplan

# Get outputs
DB_INSTANCE_ENDPOINT=$(terraform output -raw db_instance_endpoint)
DB_CREDENTIALS_SECRET_ARN=$(terraform output -raw db_credentials_secret_arn)

echo
echo "RDS instance created successfully!"
echo "Endpoint: $DB_INSTANCE_ENDPOINT"
echo "Credentials stored in AWS Secrets Manager: $DB_CREDENTIALS_SECRET_ARN"
echo
echo "To retrieve the database credentials, run:"
echo "aws secretsmanager get-secret-value --secret-id $DB_CREDENTIALS_SECRET_ARN --query SecretString --output text | jq ."
echo
echo "Next steps:"
echo "1. Update your application's database connection settings to use the new RDS instance"
echo "2. Run database migrations to set up the schema"
echo "3. Configure your application to retrieve database credentials from AWS Secrets Manager"
echo "4. Set up database monitoring and alerting"
echo "5. Configure automated backups and disaster recovery procedures"

# Clean up
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

