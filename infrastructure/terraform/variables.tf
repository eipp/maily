variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "A list of availability zones in the region"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "frontend_image" {
  description = "The Docker image for the frontend service"
  type        = string
}

variable "backend_image" {
  description = "The Docker image for the backend service"
  type        = string
}

variable "frontend_cpu" {
  description = "The number of CPU units to reserve for the frontend container"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "The amount of memory (in MiB) to reserve for the frontend container"
  type        = number
  default     = 512
}

variable "backend_cpu" {
  description = "The number of CPU units to reserve for the backend container"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "The amount of memory (in MiB) to reserve for the backend container"
  type        = number
  default     = 1024
}

variable "db_name" {
  description = "The name of the database to create"
  type        = string
  default     = "maily"
}

variable "db_username" {
  description = "The username for the database"
  type        = string
}

variable "db_password" {
  description = "The password for the database"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "The node type for the Redis cluster"
  type        = string
  default     = "cache.t3.small"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
  default     = "maily-uploads"
}

# CDN Variables
variable "cdn_custom_domain" {
  description = "Custom domain for the CDN (e.g., static.maily.app)"
  type        = string
  default     = ""
}

variable "cdn_certificate_arn" {
  description = "ARN of the ACM certificate for the CDN custom domain"
  type        = string
  default     = ""
}
