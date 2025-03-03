variable "secrets" {
  description = "Map of secret name to secret value (DEPRECATED: Use secret_names and secret_values instead)"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "secret_names" {
  description = "List of secret names to create"
  type        = list(string)
  default     = []
}

variable "secret_values" {
  description = "List of secret values corresponding to secret_names"
  type        = list(string)
  sensitive   = true
  default     = []
}

variable "environment" {
  description = "Environment name (e.g., production, staging, development)"
  type        = string
  default     = "production"
}

variable "recovery_window_in_days" {
  description = "Number of days that AWS Secrets Manager waits before it can delete the secret"
  type        = number
  default     = 30
}

variable "kms_key_id" {
  description = "ARN or Id of the AWS KMS key to be used to encrypt the secret values"
  type        = string
  default     = null
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

variable "create_env_secret" {
  description = "Whether to create a secret for the entire .env file"
  type        = bool
  default     = true
}

variable "env_file_content" {
  description = "Content of the .env file to store as a secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "create_json_secret" {
  description = "Whether to create a JSON secret with all values"
  type        = bool
  default     = true
}
