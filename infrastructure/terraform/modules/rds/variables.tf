variable "identifier" {
  description = "Identifier for the RDS instance"
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
  description = "List of subnet IDs for the DB subnet group"
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
  default     = "postgres14"
}

variable "db_parameters" {
  description = "Map of DB parameters to apply"
  type        = map(string)
  default     = {}
}

# Option group
variable "create_option_group" {
  description = "Whether to create an option group"
  type        = bool
  default     = true
}

variable "option_group_name" {
  description = "Name of an existing option group"
  type        = string
  default     = ""
}

variable "major_engine_version" {
  description = "Major engine version for the option group"
  type        = string
  default     = "14"
}

variable "db_options" {
  description = "List of DB options to apply"
  type = list(object({
    option_name = string
    option_settings = map(string)
  }))
  default = []
}

# Security group
variable "create_security_group" {
  description = "Whether to create a security group"
  type        = bool
  default     = true
}

variable "vpc_id" {
  description = "ID of the VPC where the RDS instance will be deployed"
  type        = string
  default     = ""
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the RDS instance"
  type        = list(string)
  default     = []
}

variable "allowed_security_group_ids" {
  description = "List of security group IDs allowed to access the RDS instance"
  type        = list(string)
  default     = []
}

variable "vpc_security_group_ids" {
  description = "List of existing security group IDs to associate with the RDS instance"
  type        = list(string)
  default     = []
}

# KMS key
variable "create_kms_key" {
  description = "Whether to create a KMS key for RDS encryption"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of an existing KMS key for RDS encryption"
  type        = string
  default     = ""
}

# Instance options
variable "engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "14.5"
}

variable "license_model" {
  description = "License model for the DB instance"
  type        = string
  default     = "postgresql-license"
}

variable "auto_minor_version_upgrade" {
  description = "Whether to automatically upgrade minor engine versions"
  type        = bool
  default     = true
}

variable "instance_class" {
  description = "Instance class for the RDS instance"
  type        = string
  default     = "db.t3.medium"
}

variable "storage_type" {
  description = "Storage type for the RDS instance"
  type        = string
  default     = "gp3"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage in GB for storage autoscaling"
  type        = number
  default     = 100
}

variable "port" {
  description = "Database port"
  type        = number
  default     = 5432
}

# Authentication
variable "create_random_password" {
  description = "Whether to create a random password for the master user"
  type        = bool
  default     = true
}

variable "username" {
  description = "Master username"
  type        = string
  default     = "postgres"
}

variable "password" {
  description = "Master password (if create_random_password is false)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = ""
}

variable "iam_database_authentication_enabled" {
  description = "Whether to enable IAM database authentication"
  type        = bool
  default     = true
}

variable "domain" {
  description = "Active Directory domain to join"
  type        = string
  default     = ""
}

variable "domain_iam_role_name" {
  description = "IAM role name for Active Directory domain joining"
  type        = string
  default     = ""
}

# Network
variable "multi_az" {
  description = "Whether to deploy a multi-AZ RDS instance"
  type        = bool
  default     = true
}

variable "publicly_accessible" {
  description = "Whether the DB instance is publicly accessible"
  type        = bool
  default     = false
}

# Backup and maintenance
variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-06:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:06:00-sun:10:00"
}

variable "skip_final_snapshot" {
  description = "Whether to skip the final snapshot when the instance is deleted"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Whether to enable deletion protection"
  type        = bool
  default     = true
}

# Monitoring
variable "monitoring_interval" {
  description = "Monitoring interval in seconds (0 to disable)"
  type        = number
  default     = 60
}

variable "create_monitoring_role" {
  description = "Whether to create an IAM role for enhanced monitoring"
  type        = bool
  default     = true
}

variable "monitoring_role_arn" {
  description = "ARN of an existing monitoring role"
  type        = string
  default     = null
}

variable "enabled_cloudwatch_logs_exports" {
  description = "List of log types to export to CloudWatch"
  type        = list(string)
  default     = ["postgresql", "upgrade"]
}

variable "cloudwatch_log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

variable "performance_insights_enabled" {
  description = "Whether to enable Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period in days"
  type        = number
  default     = 7
}

# CloudWatch alarms
variable "create_cloudwatch_alarms" {
  description = "Whether to create CloudWatch alarms"
  type        = bool
  default     = true
}

variable "cloudwatch_alarm_actions" {
  description = "List of ARNs to notify when the alarms trigger"
  type        = list(string)
  default     = []
}

variable "cloudwatch_ok_actions" {
  description = "List of ARNs to notify when the alarms return to OK state"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
} 