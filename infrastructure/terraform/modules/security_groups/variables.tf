variable "name" {
  description = "Name to be used as a prefix for all resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where the security groups will be created"
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

# Application Load Balancer
variable "create_alb_sg" {
  description = "Whether to create a security group for the ALB"
  type        = bool
  default     = true
}

variable "alb_ingress_cidr_blocks" {
  description = "List of CIDR blocks to allow HTTP/HTTPS traffic from"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "alb_ingress_http_enabled" {
  description = "Whether to allow HTTP traffic to the ALB"
  type        = bool
  default     = true
}

variable "alb_ingress_https_enabled" {
  description = "Whether to allow HTTPS traffic to the ALB"
  type        = bool
  default     = true
}

# ECS Tasks
variable "create_ecs_tasks_sg" {
  description = "Whether to create a security group for ECS tasks"
  type        = bool
  default     = true
}

variable "container_port" {
  description = "Port on which the container will receive traffic"
  type        = number
  default     = 80
}

variable "ecs_ingress_self_enabled" {
  description = "Whether to allow all traffic between tasks in the same security group"
  type        = bool
  default     = true
}

# Database
variable "create_database_sg" {
  description = "Whether to create a security group for the database"
  type        = bool
  default     = true
}

variable "database_port" {
  description = "Port on which the database accepts connections"
  type        = number
  default     = 5432  # Default PostgreSQL port
}

# Redis/ElastiCache
variable "create_redis_sg" {
  description = "Whether to create a security group for Redis/ElastiCache"
  type        = bool
  default     = true
}

variable "redis_port" {
  description = "Port on which Redis accepts connections"
  type        = number
  default     = 6379  # Default Redis port
}

# Bastion/VPN
variable "create_bastion_sg" {
  description = "Whether to create a security group for bastion/VPN instances"
  type        = bool
  default     = false
}

variable "bastion_ingress_cidr_blocks" {
  description = "List of CIDR blocks to allow SSH traffic from"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Consider restricting this in production
}

# Optional Access Rules
variable "allow_db_access_from_bastion" {
  description = "Whether to allow DB access from bastion hosts"
  type        = bool
  default     = true
}

variable "allow_redis_access_from_bastion" {
  description = "Whether to allow Redis access from bastion hosts"
  type        = bool
  default     = true
} 