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

variable "accelerator_name" {
  description = "The name of the Global Accelerator"
  type        = string
  default     = "maily-accelerator"
}

variable "environment" {
  description = "The deployment environment (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "flow_logs_s3_bucket" {
  description = "The S3 bucket for flow logs"
  type        = string
}

variable "flow_logs_s3_prefix" {
  description = "The S3 prefix for flow logs"
  type        = string
  default     = "flow-logs/"
}

variable "primary_traffic_dial" {
  description = "The traffic dial percentage for the primary region (0-100)"
  type        = number
  default     = 100

  validation {
    condition     = var.primary_traffic_dial >= 0 && var.primary_traffic_dial <= 100
    error_message = "The primary_traffic_dial value must be between 0 and 100."
  }
}

variable "secondary_traffic_dial" {
  description = "The traffic dial percentage for the secondary region (0-100)"
  type        = number
  default     = 100

  validation {
    condition     = var.secondary_traffic_dial >= 0 && var.secondary_traffic_dial <= 100
    error_message = "The secondary_traffic_dial value must be between 0 and 100."
  }
}

variable "primary_alb_arns" {
  description = "The ARNs of the Application Load Balancers in the primary region"
  type        = list(string)
  default     = []
}

variable "primary_nlb_arns" {
  description = "The ARNs of the Network Load Balancers in the primary region"
  type        = list(string)
  default     = []
}

variable "primary_eip_arns" {
  description = "The ARNs of the Elastic IPs in the primary region"
  type        = list(string)
  default     = []
}

variable "primary_ec2_arns" {
  description = "The ARNs of the EC2 instances in the primary region"
  type        = list(string)
  default     = []
}

variable "secondary_alb_arns" {
  description = "The ARNs of the Application Load Balancers in the secondary region"
  type        = list(string)
  default     = []
}

variable "secondary_nlb_arns" {
  description = "The ARNs of the Network Load Balancers in the secondary region"
  type        = list(string)
  default     = []
}

variable "secondary_eip_arns" {
  description = "The ARNs of the Elastic IPs in the secondary region"
  type        = list(string)
  default     = []
}

variable "secondary_ec2_arns" {
  description = "The ARNs of the EC2 instances in the secondary region"
  type        = list(string)
  default     = []
}

variable "create_dns_record" {
  description = "Whether to create a DNS record for the Global Accelerator"
  type        = bool
  default     = true
}

variable "route53_zone_id" {
  description = "The Route53 zone ID for the DNS record"
  type        = string
  default     = ""
}

variable "dns_name" {
  description = "The DNS name for the Global Accelerator"
  type        = string
  default     = "api"
}

variable "alarm_actions" {
  description = "The actions to take when the alarm is triggered"
  type        = list(string)
  default     = []
}

variable "ok_actions" {
  description = "The actions to take when the alarm returns to OK state"
  type        = list(string)
  default     = []
}

variable "bytes_threshold" {
  description = "The threshold for the processed bytes alarm"
  type        = number
  default     = 1000000000  # 1 GB
}
