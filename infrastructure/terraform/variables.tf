# Maily Infrastructure Terraform Variables

variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "domain" {
  description = "Domain name for the environment (e.g., staging.maily.ai, maily.ai)"
  type        = string
}

# VPC Variables
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# Kubernetes Variables
variable "kubernetes_version" {
  description = "Kubernetes version to use for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "kubernetes_config_path" {
  description = "Path to the Kubernetes config file"
  type        = string
  default     = "~/.kube/config"
}

# Node Group Variables
variable "standard_instance_type" {
  description = "Instance type for standard node group"
  type        = string
  default     = "t3.medium"
}

variable "standard_min_size" {
  description = "Minimum size for standard node group"
  type        = number
  default     = 2
}

variable "standard_max_size" {
  description = "Maximum size for standard node group"
  type        = number
  default     = 5
}

variable "ai_services_instance_type" {
  description = "Instance type for AI services node group"
  type        = string
  default     = "g4dn.xlarge"
}

variable "ai_services_min_size" {
  description = "Minimum size for AI services node group"
  type        = number
  default     = 1
}

variable "ai_services_max_size" {
  description = "Maximum size for AI services node group"
  type        = number
  default     = 3
}

variable "websocket_instance_type" {
  description = "Instance type for WebSocket node group"
  type        = string
  default     = "c5.large"
}

variable "websocket_min_size" {
  description = "Minimum size for WebSocket node group"
  type        = number
  default     = 1
}

variable "websocket_max_size" {
  description = "Maximum size for WebSocket node group"
  type        = number
  default     = 3
}

# Database Variables
variable "postgres_version" {
  description = "PostgreSQL version to use"
  type        = string
  default     = "15.3"
}

variable "database_instance_class" {
  description = "Instance class for the RDS instance"
  type        = string
  default     = "db.t3.medium"
}

variable "database_storage_gb" {
  description = "Storage size in GB for the RDS instance"
  type        = number
  default     = 50
}

variable "database_backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 7
}

variable "database_multi_az" {
  description = "Whether to enable multi-AZ for the RDS instance"
  type        = bool
  default     = false
}

variable "database_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

# Redis Variables
variable "redis_version" {
  description = "Redis version to use"
  type        = string
  default     = "7.0"
}

variable "redis_instance_type" {
  description = "Instance type for Redis"
  type        = string
  default     = "cache.t3.small"
}

variable "redis_replicas_per_shard" {
  description = "Number of replicas per shard for Redis"
  type        = number
  default     = 1
}

# Vercel Variables
variable "vercel_token" {
  description = "Vercel API token"
  type        = string
  sensitive   = true
}

variable "vercel_team_id" {
  description = "Vercel team ID"
  type        = string
}

# Supabase Variables
variable "supabase_url" {
  description = "Supabase URL"
  type        = string
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
}

# Monitoring Variables
variable "datadog_api_key" {
  description = "Datadog API key"
  type        = string
  sensitive   = true
}

variable "datadog_app_key" {
  description = "Datadog application key"
  type        = string
  sensitive   = true
}

variable "prometheus_retention_days" {
  description = "Number of days to retain Prometheus data"
  type        = number
  default     = 15
}

variable "prometheus_scrape_interval" {
  description = "Prometheus scrape interval in seconds"
  type        = number
  default     = 15
}

variable "grafana_version" {
  description = "Grafana version to use"
  type        = string
  default     = "10.0.3"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

# Vault Variables
variable "vault_version" {
  description = "Vault version to use"
  type        = string
  default     = "1.14.0"
}
