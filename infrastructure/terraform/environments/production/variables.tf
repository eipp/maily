variable "cluster_name" {
  description = "The name of the EKS cluster"
  type        = string
  default     = "maily-production-cluster"
}

variable "key_name" {
  description = "The name of the EC2 key pair to use for Vault instances"
  type        = string
}

variable "certificate_arn" {
  description = "The ARN of the ACM certificate to use for the CDN"
  type        = string
}

variable "domain_name" {
  description = "The domain name for the application"
  type        = string
  default     = "maily.com"
}

variable "enable_waf" {
  description = "Whether to enable AWS WAF for the API Gateway"
  type        = bool
  default     = true
}

variable "environment" {
  description = "The environment name"
  type        = string
  default     = "production"
}

variable "ecr_repository_url" {
  description = "The URL of the ECR repository where container images are stored"
  type        = string
}

variable "db_instance_type" {
  description = "The instance type to use for the database"
  type        = string
  default     = "db.r5.large"
}

variable "db_storage" {
  description = "The allocated storage for the database (in GB)"
  type        = number
  default     = 100
}

variable "db_multi_az" {
  description = "Whether to enable Multi-AZ for the database"
  type        = bool
  default     = true
}

variable "redis_instance_type" {
  description = "The instance type to use for Redis"
  type        = string
  default     = "cache.r5.large"
}

variable "redis_nodes" {
  description = "The number of cache nodes for Redis"
  type        = number
  default     = 3
}
