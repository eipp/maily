variable "name" {
  description = "Name to be used on all resources as prefix"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}

# ECS Cluster
variable "create_cluster" {
  description = "Whether to create a new ECS cluster"
  type        = bool
  default     = true
}

variable "cluster_id" {
  description = "ID of existing ECS cluster to use if create_cluster is false"
  type        = string
  default     = null
}

variable "enable_container_insights" {
  description = "Whether to enable container insights for the ECS cluster"
  type        = bool
  default     = true
}

variable "execute_command_kms_key_id" {
  description = "KMS key ID for execute command encryption"
  type        = string
  default     = null
}

variable "execute_command_logging" {
  description = "Logging configuration for execute command. Valid values: NONE, DEFAULT, OVERRIDE"
  type        = string
  default     = "DEFAULT"
  validation {
    condition     = contains(["NONE", "DEFAULT", "OVERRIDE"], var.execute_command_logging)
    error_message = "Valid values for execute_command_logging are NONE, DEFAULT, or OVERRIDE."
  }
}

variable "execute_command_log_encryption" {
  description = "Whether to encrypt execute command logs"
  type        = bool
  default     = true
}

variable "fargate_capacity_providers" {
  description = "List of Fargate capacity providers to use"
  type        = list(string)
  default     = ["FARGATE", "FARGATE_SPOT"]
}

variable "default_capacity_provider" {
  description = "Default capacity provider to use"
  type        = string
  default     = "FARGATE"
}

variable "default_capacity_provider_strategy_base" {
  description = "Base value for the default capacity provider strategy"
  type        = number
  default     = 1
}

variable "default_capacity_provider_strategy_weight" {
  description = "Weight value for the default capacity provider strategy"
  type        = number
  default     = 100
}

# Container Definition
variable "container_name" {
  description = "Name of the container"
  type        = string
}

variable "container_image" {
  description = "Docker image to run"
  type        = string
}

variable "container_cpu" {
  description = "CPU units to allocate to the container"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory to allocate to the container (hard limit)"
  type        = number
  default     = 512
}

variable "container_memory_reservation" {
  description = "Memory to allocate to the container (soft limit)"
  type        = number
  default     = null
}

variable "container_port" {
  description = "Port to expose on the container"
  type        = number
}

variable "container_privileged" {
  description = "Whether to give the container elevated privileges"
  type        = bool
  default     = false
}

variable "container_readonly_root_filesystem" {
  description = "Whether to make the container root filesystem read-only"
  type        = bool
  default     = false
}

variable "environment_variables" {
  description = "Environment variables to pass to the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets to pass to the container"
  type        = map(string)
  default     = {}
}

variable "secret_arns" {
  description = "ARNs of secrets and KMS keys"
  type        = list(string)
  default     = []
}

variable "enable_container_healthcheck" {
  description = "Whether to enable the container healthcheck"
  type        = bool
  default     = true
}

variable "healthcheck_command" {
  description = "Command to run for the container healthcheck"
  type        = list(string)
  default     = ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]
}

variable "healthcheck_interval" {
  description = "Time between healthcheck runs (seconds)"
  type        = number
  default     = 30
}

variable "healthcheck_timeout" {
  description = "Time to wait for a healthcheck to succeed before failing (seconds)"
  type        = number
  default     = 5
}

variable "healthcheck_retries" {
  description = "Number of retries for a failing healthcheck before marking unhealthy"
  type        = number
  default     = 3
}

variable "healthcheck_start_period" {
  description = "Grace period within which failed healthchecks are not counted (seconds)"
  type        = number
  default     = 60
}

# Task Definition
variable "task_cpu" {
  description = "CPU units to allocate to the task"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory to allocate to the task"
  type        = number
  default     = 512
}

variable "create_iam_roles" {
  description = "Whether to create IAM roles for the ECS task"
  type        = bool
  default     = true
}

variable "execution_role_arn" {
  description = "ARN of the task execution role to use if create_iam_roles is false"
  type        = string
  default     = null
}

variable "task_role_arn" {
  description = "ARN of the task role to use if create_iam_roles is false"
  type        = string
  default     = null
}

variable "task_role_policy" {
  description = "Policy to attach to the task role"
  type        = string
  default     = null
}

variable "ephemeral_storage_size" {
  description = "Size of ephemeral storage in GiB (0 to use default)"
  type        = number
  default     = 0
}

variable "volumes" {
  description = "List of volumes to attach to the task"
  type        = any
  default     = []
}

variable "placement_constraints" {
  description = "Placement constraints for the task"
  type        = list(any)
  default     = []
}

variable "proxy_configuration" {
  description = "App Mesh proxy configuration for the task"
  type        = any
  default     = null
}

# ECS Service
variable "desired_count" {
  description = "Number of task instances to run"
  type        = number
  default     = 1
}

variable "force_new_deployment" {
  description = "Whether to force a new deployment of the service"
  type        = bool
  default     = false
}

variable "deployment_minimum_healthy_percent" {
  description = "Minimum percent of tasks that must remain healthy during deployment"
  type        = number
  default     = 100
}

variable "deployment_maximum_percent" {
  description = "Maximum percent of tasks that can be running during deployment"
  type        = number
  default     = 200
}

variable "health_check_grace_period_seconds" {
  description = "Seconds to wait before checking task health"
  type        = number
  default     = 60
}

variable "enable_execute_command" {
  description = "Whether to enable the ECS Exec feature"
  type        = bool
  default     = false
}

variable "enable_ecs_managed_tags" {
  description = "Whether to enable ECS managed tags"
  type        = bool
  default     = true
}

variable "platform_version" {
  description = "Platform version for the service (Fargate)"
  type        = string
  default     = "LATEST"
}

variable "subnet_ids" {
  description = "Subnet IDs to launch the task in"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs to assign to the task"
  type        = list(string)
}

variable "assign_public_ip" {
  description = "Whether to assign a public IP to the task"
  type        = bool
  default     = false
}

variable "capacity_provider_strategy" {
  description = "Capacity provider strategy for the service"
  type        = list(any)
  default     = []
}

variable "lb_target_group_arn" {
  description = "ARN of the load balancer target group to associate with the service"
  type        = string
  default     = null
}

variable "service_registry_arn" {
  description = "ARN of the service registry (Cloud Map) to associate with the service"
  type        = string
  default     = null
}

variable "service_registry_container_name" {
  description = "Container name for service registry"
  type        = string
  default     = null
}

variable "service_registry_container_port" {
  description = "Container port for service registry"
  type        = number
  default     = null
}

variable "deployment_controller_type" {
  description = "Type of deployment controller. Valid values: ECS, CODE_DEPLOY, EXTERNAL"
  type        = string
  default     = "ECS"
  validation {
    condition     = contains(["ECS", "CODE_DEPLOY", "EXTERNAL"], var.deployment_controller_type)
    error_message = "Valid values for deployment_controller_type are ECS, CODE_DEPLOY, or EXTERNAL."
  }
}

# CloudWatch
variable "log_retention_in_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

variable "log_kms_key_id" {
  description = "KMS key ID for log encryption"
  type        = string
  default     = null
}

variable "create_alarms" {
  description = "Whether to create CloudWatch alarms"
  type        = bool
  default     = true
}

variable "cpu_utilization_high_threshold" {
  description = "Threshold for CPU utilization alarm"
  type        = number
  default     = 80
}

variable "memory_utilization_high_threshold" {
  description = "Threshold for memory utilization alarm"
  type        = number
  default     = 80
}

variable "alarm_actions" {
  description = "List of ARNs to notify for alarm actions"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "List of ARNs to notify for OK actions"
  type        = list(string)
  default     = []
}

# AutoScaling
variable "enable_autoscaling" {
  description = "Whether to enable autoscaling for the service"
  type        = bool
  default     = false
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks for autoscaling"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks for autoscaling"
  type        = number
  default     = 10
}

variable "autoscaling_cpu_enabled" {
  description = "Whether to enable CPU-based autoscaling"
  type        = bool
  default     = true
}

variable "autoscaling_cpu_target_value" {
  description = "Target CPU utilization for autoscaling"
  type        = number
  default     = 70
}

variable "autoscaling_memory_enabled" {
  description = "Whether to enable memory-based autoscaling"
  type        = bool
  default     = true
}

variable "autoscaling_memory_target_value" {
  description = "Target memory utilization for autoscaling"
  type        = number
  default     = 70
}

variable "autoscaling_requests_enabled" {
  description = "Whether to enable request count-based autoscaling"
  type        = bool
  default     = false
}

variable "autoscaling_requests_target_value" {
  description = "Target request count per target for autoscaling"
  type        = number
  default     = 1000
}

variable "autoscaling_scale_in_cooldown" {
  description = "Cooldown period in seconds after scaling in"
  type        = number
  default     = 300
}

variable "autoscaling_scale_out_cooldown" {
  description = "Cooldown period in seconds after scaling out"
  type        = number
  default     = 300
}

variable "alb_arn_suffix" {
  description = "ARN suffix of the ALB for request-based autoscaling"
  type        = string
  default     = null
}

variable "lb_target_group_arn_suffix" {
  description = "ARN suffix of the target group for request-based autoscaling"
  type        = string
  default     = null
} 