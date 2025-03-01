variable "primary_region" {
  description = "The primary AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "secondary_region" {
  description = "The secondary AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "mesh_name" {
  description = "The name of the App Mesh service mesh"
  type        = string
  default     = "maily-mesh"
}

variable "domain_name" {
  description = "The domain name for service discovery"
  type        = string
}

variable "environment" {
  description = "The deployment environment (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "primary_weight" {
  description = "The routing weight for the primary region (0-100)"
  type        = number
  default     = 50

  validation {
    condition     = var.primary_weight >= 0 && var.primary_weight <= 100
    error_message = "The primary_weight value must be between 0 and 100."
  }
}

variable "secondary_weight" {
  description = "The routing weight for the secondary region (0-100)"
  type        = number
  default     = 50

  validation {
    condition     = var.secondary_weight >= 0 && var.secondary_weight <= 100
    error_message = "The secondary_weight value must be between 0 and 100."
  }
}

variable "vpc_id" {
  description = "The VPC ID for the primary region"
  type        = string
}

variable "secondary_vpc_id" {
  description = "The VPC ID for the secondary region"
  type        = string
}

variable "subnet_ids" {
  description = "The subnet IDs for the primary region"
  type        = list(string)
}

variable "secondary_subnet_ids" {
  description = "The subnet IDs for the secondary region"
  type        = list(string)
}
