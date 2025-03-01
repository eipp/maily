variable "project_name" {
  description = "The name of the project (e.g., maily)"
  type        = string
  default     = "maily"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "custom_domain" {
  description = "Custom domain for the CDN (e.g., static.maily.app)"
  type        = string
  default     = ""
}

variable "cache_behaviors" {
  description = "List of path patterns for cache behaviors (e.g., ['*.jpg', '*.css'])"
  type        = list(string)
  default     = ["*.jpg", "*.css", "*.js", "*.woff", "*.woff2", "*.ttf", "*.eot"]
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for the custom domain"
  type        = string
  default     = ""
}
