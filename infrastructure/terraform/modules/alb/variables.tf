variable "name" {
  description = "Name to be used for resources and tags"
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

# ALB Configuration
variable "internal" {
  description = "Whether the load balancer is internal or internet-facing"
  type        = bool
  default     = false
}

variable "security_group_id" {
  description = "ID of the security group for the ALB"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the ALB"
  type        = list(string)
}

variable "vpc_id" {
  description = "ID of the VPC where the ALB will be created"
  type        = string
}

variable "enable_deletion_protection" {
  description = "Whether to enable deletion protection on the ALB"
  type        = bool
  default     = true
}

variable "enable_cross_zone_load_balancing" {
  description = "Whether to enable cross-zone load balancing"
  type        = bool
  default     = true
}

variable "enable_http2" {
  description = "Whether to enable HTTP/2"
  type        = bool
  default     = true
}

variable "idle_timeout" {
  description = "The time in seconds that the connection is allowed to be idle"
  type        = number
  default     = 60
}

variable "drop_invalid_header_fields" {
  description = "Whether to drop invalid header fields"
  type        = bool
  default     = true
}

variable "desync_mitigation_mode" {
  description = "How the load balancer handles requests that might pose a security risk. Valid values are 'defensive', 'strictest', and 'monitor'"
  type        = string
  default     = "defensive"
  validation {
    condition     = contains(["defensive", "strictest", "monitor"], var.desync_mitigation_mode)
    error_message = "Valid values for desync_mitigation_mode are 'defensive', 'strictest', and 'monitor'."
  }
}

# Access Logs
variable "access_logs_bucket" {
  description = "S3 bucket name for ALB access logs"
  type        = string
  default     = null
}

variable "access_logs_prefix" {
  description = "S3 bucket prefix for ALB access logs"
  type        = string
  default     = "logs/alb"
}

# HTTP Listener
variable "create_http_listener" {
  description = "Whether to create HTTP listener"
  type        = bool
  default     = true
}

variable "redirect_http_to_https" {
  description = "Whether to redirect HTTP to HTTPS"
  type        = bool
  default     = true
}

# HTTPS Listener
variable "create_https_listener" {
  description = "Whether to create HTTPS listener"
  type        = bool
  default     = true
}

variable "ssl_policy" {
  description = "SSL policy for HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS-1-2-2017-01"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
  default     = null
}

# Default Target Group
variable "target_group_port" {
  description = "Port for the default target group"
  type        = number
  default     = 80
}

variable "target_group_protocol" {
  description = "Protocol for the default target group"
  type        = string
  default     = "HTTP"
}

variable "target_type" {
  description = "Type of target for the default target group"
  type        = string
  default     = "ip"
  validation {
    condition     = contains(["instance", "ip", "lambda", "alb"], var.target_type)
    error_message = "Valid values for target_type are 'instance', 'ip', 'lambda', and 'alb'."
  }
}

variable "deregistration_delay" {
  description = "Amount of time for Elastic Load Balancing to wait before changing the state of a deregistering target from draining to unused"
  type        = number
  default     = 300
}

# Health Check
variable "health_check_interval" {
  description = "Approximate amount of time, in seconds, between health checks of an individual target"
  type        = number
  default     = 30
}

variable "health_check_path" {
  description = "Path for health check requests"
  type        = string
  default     = "/"
}

variable "health_check_port" {
  description = "Port for health check requests"
  type        = string
  default     = "traffic-port"
}

variable "health_check_protocol" {
  description = "Protocol for health check requests"
  type        = string
  default     = "HTTP"
}

variable "health_check_timeout" {
  description = "Amount of time, in seconds, during which no response means a failed health check"
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive health checks successes required before considering an unhealthy target healthy"
  type        = number
  default     = 3
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive health check failures required before considering the target unhealthy"
  type        = number
  default     = 3
}

variable "health_check_matcher" {
  description = "HTTP codes to use when checking for a successful response from a target"
  type        = string
  default     = "200-299"
}

# Stickiness
variable "stickiness_enabled" {
  description = "Whether stickiness is enabled for the default target group"
  type        = bool
  default     = false
}

variable "stickiness_type" {
  description = "Type of stickiness"
  type        = string
  default     = "lb_cookie"
}

variable "stickiness_cookie_duration" {
  description = "Lifetime of the stickiness cookie in seconds"
  type        = number
  default     = 86400 # 1 day
}

# Additional Target Groups
variable "additional_target_groups" {
  description = "List of additional target groups"
  type        = list(any)
  default     = []
}

# Path Patterns
variable "path_patterns" {
  description = "List of path patterns for listener rules"
  type        = list(any)
  default     = []
}

# Monitoring and Alarms
variable "create_alarms" {
  description = "Whether to create CloudWatch alarms"
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

variable "alarm_5xx_threshold" {
  description = "Threshold for 5XX errors alarm"
  type        = number
  default     = 10
}

variable "alarm_4xx_threshold" {
  description = "Threshold for 4XX errors alarm"
  type        = number
  default     = 50
}

variable "alarm_target_5xx_threshold" {
  description = "Threshold for target 5XX errors alarm"
  type        = number
  default     = 10
}

variable "alarm_unhealthy_hosts_threshold" {
  description = "Threshold for unhealthy hosts alarm"
  type        = number
  default     = 1
}

# WAF
variable "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL to associate with the ALB"
  type        = string
  default     = null
} 