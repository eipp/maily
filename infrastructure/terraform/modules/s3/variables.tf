variable "name" {
  description = "Name to be used for resources and tags"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

# KMS Key Configuration
variable "create_kms_key" {
  description = "Whether to create a KMS key for S3 bucket encryption"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "ARN of the KMS key to use for encryption if create_kms_key is false"
  type        = string
  default     = null
}

variable "kms_key_deletion_window_in_days" {
  description = "The waiting period, specified in number of days, before the KMS key is deleted"
  type        = number
  default     = 30
}

variable "kms_key_enable_rotation" {
  description = "Whether KMS key rotation is enabled"
  type        = bool
  default     = true
}

variable "kms_key_policy" {
  description = "A KMS key policy as a JSON formatted string"
  type        = string
  default     = null
}

# Bucket Configuration
variable "block_public_acls" {
  description = "Whether Amazon S3 should block public ACLs for this bucket"
  type        = bool
  default     = true
}

variable "block_public_policy" {
  description = "Whether Amazon S3 should block public bucket policies for this bucket"
  type        = bool
  default     = true
}

variable "ignore_public_acls" {
  description = "Whether Amazon S3 should ignore public ACLs for this bucket"
  type        = bool
  default     = true
}

variable "restrict_public_buckets" {
  description = "Whether Amazon S3 should restrict public bucket policies for this bucket"
  type        = bool
  default     = true
}

variable "versioning_enabled" {
  description = "Whether S3 bucket versioning is enabled"
  type        = bool
  default     = true
}

variable "bucket_key_enabled" {
  description = "Whether to use S3 bucket keys for SSE-KMS"
  type        = bool
  default     = true
}

# Lifecycle Rules
variable "lifecycle_rules" {
  description = "List of lifecycle rules for bucket objects"
  type = list(object({
    id      = string
    enabled = bool
    expiration = optional(object({
      days = number
    }))
    transitions = optional(list(object({
      days          = number
      storage_class = string
    })))
    noncurrent_version_expiration = optional(object({
      days = number
    }))
    noncurrent_version_transitions = optional(list(object({
      days          = number
      storage_class = string
    })))
    abort_incomplete_multipart_upload_days = optional(number)
  }))
  default = []
}

# Access Logging
variable "access_log_bucket_name" {
  description = "Name of the S3 bucket where access logs will be delivered"
  type        = string
  default     = null
}

variable "access_log_prefix" {
  description = "Prefix for all log object keys"
  type        = string
  default     = "logs/"
}

# Bucket Policy
variable "attach_policy" {
  description = "Whether to attach a policy to the bucket"
  type        = bool
  default     = false
}

variable "policy" {
  description = "A bucket policy in JSON format"
  type        = string
  default     = null
}

variable "enforce_ssl" {
  description = "Whether to enforce SSL/TLS for all operations with the bucket"
  type        = bool
  default     = true
}

# Monitoring
variable "create_monitoring_alarms" {
  description = "Whether to create CloudWatch alarms for the bucket"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "List of ARNs to notify for alarm actions"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs to notify for ok actions"
  type        = list(string)
  default     = []
} 