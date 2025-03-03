#!/bin/bash
# setup-redis-cluster.sh
# Script to set up a Redis cluster for Maily

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
CLUSTER_NAME="maily-redis"
NODE_TYPE="cache.t3.medium"
NUM_SHARDS=2
REPLICAS_PER_SHARD=1
ENGINE_VERSION="6.2"
PARAMETER_GROUP_NAME="default.redis6.x.cluster.on"
SUBNET_GROUP_NAME="maily-redis-subnet-group"
SECURITY_GROUP_NAME="maily-redis-sg"
ENVIRONMENT="production"
PROJECT_NAME="maily"
MAINTENANCE_WINDOW="sun:05:00-sun:06:00"
SNAPSHOT_WINDOW="03:00-04:00"
SNAPSHOT_RETENTION_LIMIT=7
AUTO_MINOR_VERSION_UPGRADE=true
MULTI_AZ_ENABLED=true
AUTOMATIC_FAILOVER_ENABLED=true
TRANSIT_ENCRYPTION_ENABLED=true
AT_REST_ENCRYPTION_ENABLED=true
APPLY_IMMEDIATELY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --cluster-name)
      CLUSTER_NAME="$2"
      shift 2
      ;;
    --node-type)
      NODE_TYPE="$2"
      shift 2
      ;;
    --num-shards)
      NUM_SHARDS="$2"
      shift 2
      ;;
    --replicas-per-shard)
      REPLICAS_PER_SHARD="$2"
      shift 2
      ;;
    --engine-version)
      ENGINE_VERSION="$2"
      shift 2
      ;;
    --parameter-group-name)
      PARAMETER_GROUP_NAME="$2"
      shift 2
      ;;
    --subnet-group-name)
      SUBNET_GROUP_NAME="$2"
      shift 2
      ;;
    --security-group-name)
      SECURITY_GROUP_NAME="$2"
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
    --maintenance-window)
      MAINTENANCE_WINDOW="$2"
      shift 2
      ;;
    --snapshot-window)
      SNAPSHOT_WINDOW="$2"
      shift 2
      ;;
    --snapshot-retention-limit)
      SNAPSHOT_RETENTION_LIMIT="$2"
      shift 2
      ;;
    --auto-minor-version-upgrade)
      AUTO_MINOR_VERSION_UPGRADE="$2"
      shift 2
      ;;
    --multi-az-enabled)
      MULTI_AZ_ENABLED="$2"
      shift 2
      ;;
    --automatic-failover-enabled)
      AUTOMATIC_FAILOVER_ENABLED="$2"
      shift 2
      ;;
    --transit-encryption-enabled)
      TRANSIT_ENCRYPTION_ENABLED="$2"
      shift 2
      ;;
    --at-rest-encryption-enabled)
      AT_REST_ENCRYPTION_ENABLED="$2"
      shift 2
      ;;
    --apply-immediately)
      APPLY_IMMEDIATELY="$2"
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

resource "aws_elasticache_subnet_group" "main" {
  name       = "${SUBNET_GROUP_NAME}"
  subnet_ids = data.aws_subnets.private.ids

  tags = {
    Name        = "${SUBNET_GROUP_NAME}"
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "aws_security_group" "redis" {
  name        = "${SECURITY_GROUP_NAME}"
  description = "Security group for ${PROJECT_NAME} ${ENVIRONMENT} Redis cluster"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "Allow Redis traffic from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "${SECURITY_GROUP_NAME}"
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "random_password" "redis_auth_token" {
  length           = 32
  special          = false
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "redis_credentials" {
  name        = "${PROJECT_NAME}/${ENVIRONMENT}/redis-credentials"
  description = "Redis credentials for ${PROJECT_NAME} ${ENVIRONMENT}"
  
  tags = {
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
    host       = aws_elasticache_replication_group.main.configuration_endpoint_address
    port       = 6379
    clusterName = aws_elasticache_replication_group.main.id
  })
}

resource "aws_elasticache_parameter_group" "main" {
  name   = "${PROJECT_NAME}-${ENVIRONMENT}-redis6-params"
  family = "redis6.x"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  parameter {
    name  = "notify-keyspace-events"
    value = "KEA"
  }

  tags = {
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${CLUSTER_NAME}"
  description                = "Redis cluster for ${PROJECT_NAME} ${ENVIRONMENT}"
  node_type                  = "${NODE_TYPE}"
  num_node_groups            = ${NUM_SHARDS}
  replicas_per_node_group    = ${REPLICAS_PER_SHARD}
  engine_version             = "${ENGINE_VERSION}"
  parameter_group_name       = "${PARAMETER_GROUP_NAME}"
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  maintenance_window         = "${MAINTENANCE_WINDOW}"
  snapshot_window            = "${SNAPSHOT_WINDOW}"
  snapshot_retention_limit   = ${SNAPSHOT_RETENTION_LIMIT}
  auto_minor_version_upgrade = ${AUTO_MINOR_VERSION_UPGRADE}
  multi_az_enabled           = ${MULTI_AZ_ENABLED}
  automatic_failover_enabled = ${AUTOMATIC_FAILOVER_ENABLED}
  transit_encryption_enabled = ${TRANSIT_ENCRYPTION_ENABLED}
  at_rest_encryption_enabled = ${AT_REST_ENCRYPTION_ENABLED}
  apply_immediately          = ${APPLY_IMMEDIATELY}
  auth_token                 = random_password.redis_auth_token.result

  tags = {
    Name        = "${CLUSTER_NAME}"
    Environment = "${ENVIRONMENT}"
    Project     = "${PROJECT_NAME}"
    ManagedBy   = "Terraform"
  }
}

output "redis_endpoint" {
  description = "The configuration endpoint of the Redis cluster"
  value       = aws_elasticache_replication_group.main.configuration_endpoint_address
}

output "redis_port" {
  description = "The port of the Redis cluster"
  value       = 6379
}

output "redis_credentials_secret_arn" {
  description = "The ARN of the Secrets Manager secret storing the Redis credentials"
  value       = aws_secretsmanager_secret.redis_credentials.arn
}
EOF

# Initialize and apply Terraform
cd $TEMP_DIR
echo "Initializing Terraform..."
terraform init

echo "Planning Terraform deployment..."
terraform plan -out=tfplan

# Ask for confirmation before applying
read -p "Do you want to apply the Terraform plan and create the Redis cluster? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Redis cluster setup cancelled."
  exit 0
fi

echo "Applying Terraform plan..."
terraform apply tfplan

# Get outputs
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
REDIS_CREDENTIALS_SECRET_ARN=$(terraform output -raw redis_credentials_secret_arn)

echo
echo "Redis cluster created successfully!"
echo "Endpoint: $REDIS_ENDPOINT"
echo "Port: 6379"
echo "Credentials stored in AWS Secrets Manager: $REDIS_CREDENTIALS_SECRET_ARN"
echo
echo "To retrieve the Redis credentials, run:"
echo "aws secretsmanager get-secret-value --secret-id $REDIS_CREDENTIALS_SECRET_ARN --query SecretString --output text | jq ."
echo
echo "Next steps:"
echo "1. Update your application's Redis connection settings to use the new Redis cluster"
echo "2. Configure your application to retrieve Redis credentials from AWS Secrets Manager"
echo "3. Set up Redis monitoring and alerting"
echo "4. Configure Redis backup and recovery procedures"
echo "5. Test Redis connectivity and performance"

# Create Kubernetes ConfigMap and Secret for Redis
echo "Creating Kubernetes ConfigMap and Secret for Redis..."

# Create ConfigMap
cat > redis-configmap.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: ${ENVIRONMENT}
data:
  REDIS_HOST: "${REDIS_ENDPOINT}"
  REDIS_PORT: "6379"
EOF

# Create Secret
cat > redis-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: redis-secret
  namespace: ${ENVIRONMENT}
type: Opaque
stringData:
  REDIS_AUTH_TOKEN: "$(aws secretsmanager get-secret-value --secret-id $REDIS_CREDENTIALS_SECRET_ARN --query 'SecretString' --output text | jq -r '.auth_token')"
EOF

echo "Kubernetes ConfigMap and Secret files created:"
echo "- redis-configmap.yaml"
echo "- redis-secret.yaml"
echo
echo "To apply these to your Kubernetes cluster, run:"
echo "kubectl apply -f redis-configmap.yaml"
echo "kubectl apply -f redis-secret.yaml"

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

