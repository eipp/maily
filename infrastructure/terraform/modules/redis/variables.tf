variable "name" {
  description = "Name for the Redis cluster"
  type        = string
}

variable "env" {
  description = "Environment name"
  type        = string
}

# Subnet group
variable "create_subnet_group" {
  description = "Whether to create a subnet group"
  type        = bool
  default     = true
}

variable "subnet_group_name" {
  description = "Name of an existing subnet group"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "List of subnet IDs for the subnet group"
  type        = list(string)
  default     = []
}

# Parameter group
variable "create_parameter_group" {
  description = "Whether to create a parameter group"
  type        = bool
  default     = true
}

variable "parameter_group_name" {
  description = "Name of an existing parameter group"
  type        = string
  default     = ""
}

variable "parameter_group_family" {
  description = "Family of the parameter group"
  type        = string
  default     = "redis7"
}

variable "parameter_group_parameters" {
  description = "Map of parameter group parameters"
  type        = map(string)
  default     = {}
}

# Security group
variable "create_security_group" {
  description = "Whether to create a security group"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "ID of the VPC where the Redis cluster will be deployed"
  type        = string
  default     = ""
}

variable "allowed_security_group_ids" {
  description = "List of security group IDs allowed to access the Redis cluster"
  type        = list(string)
  default     = []
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the Redis cluster"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of existing security group IDs to associate with the Redis cluster"
  type        = list(string)
  default     = []
}

# KMS key
variable "create_kms_key" {
  description = "Whether to create a KMS key for Redis encryption"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "ARN of an existing KMS key for Redis encryption"
  type        = string
  default     = ""
}

# Redis cluster options
variable "node_type" {
  description = "Node type for the Redis cluster"
  type        = string
  default     = "cache.t3.medium"
}

variable "port" {
  description = "Port for the Redis cluster"
  type        = number
  default     = 6379
}

variable "engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "auth_token" {
  description = "Auth token for transit encryption"
  type        = string
  default     = null
  sensitive   = true
}

variable "automatic_failover_enabled" {
  description = "Whether to enable automatic failover"
  type        = bool
  default     = true
}

variable "multi_az_enabled" {
  description = "Whether to enable Multi-AZ"
  type        = bool
  default     = true
}

variable "num_cache_clusters" {
  description = "Number of cache clusters (nodes) in the replication group"
  type        = number
  default     = 2
}

variable "maintenance_window" {
  description = "Maintenance window"
  type        = string
  default     = "sun:05:00-sun:09:00"
}

variable "snapshot_window" {
  description = "Snapshot window"
  type        = string
  default     = "00:00-04:00"
}

variable "snapshot_retention_limit" {
  description = "Number of days for which ElastiCache retains snapshots"
  type        = number
  default     = 30
}

variable "auto_minor_version_upgrade" {
  description = "Whether to automatically upgrade minor versions"
  type        = bool
  default     = true
}

variable "apply_immediately" {
  description = "Whether to apply changes immediately or during the maintenance window"
  type        = bool
  default     = false
}

variable "data_tiering_enabled" {
  description = "Whether to enable data tiering (only compatible with r6gd nodes)"
  type        = bool
  default     = false
}

variable "preferred_cache_cluster_azs" {
  description = "List of preferred AZs for cache clusters"
  type        = list(string)
  default     = null
}

# Monitoring
variable "notification_topic_arn" {
  description = "ARN of an SNS topic for Redis notifications"
  type        = string
  default     = ""
}

variable "create_cloudwatch_alarms" {
  description = "Whether to create CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "List of ARNs to notify when an alarm is triggered"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs to notify when an alarm returns to OK state"
  type        = list(string)
  default     = []
}

variable "max_connections_threshold" {
  description = "Threshold for the high connections alarm"
  type        = number
  default     = 5000
}

# Serverless
variable "serverless_enabled" {
  description = "Whether to enable serverless caching"
  type        = bool
  default     = false
}

variable "serverless_max_cache_memory_usage_gb" {
  description = "Maximum memory usage in GB for serverless caching"
  type        = number
  default     = 5
}

# Log delivery
variable "enable_log_delivery" {
  description = "Whether to enable log delivery"
  type        = bool
  default     = false
}

variable "log_delivery_destination" {
  description = "Destination for log delivery"
  type        = string
  default     = ""
}

variable "log_delivery_destination_type" {
  description = "Type of destination for log delivery (cloudwatch-logs, kinesis-firehose)"
  type        = string
  default     = "cloudwatch-logs"
}

variable "log_delivery_format" {
  description = "Format for log delivery (json, text)"
  type        = string
  default     = "json"
}

variable "log_delivery_type" {
  description = "Type of logs to export (engine-log, slow-log)"
  type        = string
  default     = "engine-log"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
} 