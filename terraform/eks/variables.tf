variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "maily"
}

variable "environment" {
  description = "Environment name (e.g., production, staging, development)"
  type        = string
  default     = "production"
}

variable "kubernetes_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.28"
}

# General Node Group Variables
variable "general_node_group_desired_size" {
  description = "Desired number of nodes in the general node group"
  type        = number
  default     = 2
}

variable "general_node_group_max_size" {
  description = "Maximum number of nodes in the general node group"
  type        = number
  default     = 4
}

variable "general_node_group_min_size" {
  description = "Minimum number of nodes in the general node group"
  type        = number
  default     = 1
}

variable "general_node_group_instance_types" {
  description = "Instance types for the general node group"
  type        = list(string)
  default     = ["t3.medium"]
}

# Services Node Group Variables
variable "services_node_group_desired_size" {
  description = "Desired number of nodes in the services node group"
  type        = number
  default     = 2
}

variable "services_node_group_max_size" {
  description = "Maximum number of nodes in the services node group"
  type        = number
  default     = 6
}

variable "services_node_group_min_size" {
  description = "Minimum number of nodes in the services node group"
  type        = number
  default     = 1
}

variable "services_node_group_instance_types" {
  description = "Instance types for the services node group"
  type        = list(string)
  default     = ["t3.large"]
}

# Endpoint Access Variables
variable "endpoint_private_access" {
  description = "Whether the Amazon EKS private API server endpoint is enabled"
  type        = bool
  default     = true
}

variable "endpoint_public_access" {
  description = "Whether the Amazon EKS public API server endpoint is enabled"
  type        = bool
  default     = true
}

variable "public_access_cidrs" {
  description = "List of CIDR blocks which can access the Amazon EKS public API server endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Logging Variables
variable "enabled_cluster_log_types" {
  description = "List of the desired control plane logging to enable"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "log_retention_days" {
  description = "Number of days to retain log events"
  type        = number
  default     = 30
}

# Tags
variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}
