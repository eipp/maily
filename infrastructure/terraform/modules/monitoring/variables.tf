# Maily Monitoring Module Variables

variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
}

variable "domain" {
  description = "Domain name for the environment (e.g., staging.maily.ai, maily.ai)"
  type        = string
}

# Prometheus Variables
variable "prometheus_chart_version" {
  description = "Version of the Prometheus Helm chart"
  type        = string
  default     = "45.7.1"  # kube-prometheus-stack chart version
}

variable "prometheus_retention_days" {
  description = "Number of days to retain Prometheus data"
  type        = number
  default     = 15
}

variable "prometheus_scrape_interval" {
  description = "Prometheus scrape interval in seconds"
  type        = number
  default     = 15
}

# Grafana Variables
variable "grafana_version" {
  description = "Grafana version to use"
  type        = string
  default     = "10.0.3"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

# Datadog Variables
variable "datadog_chart_version" {
  description = "Version of the Datadog Helm chart"
  type        = string
  default     = "3.36.0"
}

variable "datadog_api_key" {
  description = "Datadog API key"
  type        = string
  sensitive   = true
}

variable "datadog_app_key" {
  description = "Datadog application key"
  type        = string
  sensitive   = true
}

# Loki Variables
variable "loki_chart_version" {
  description = "Version of the Loki Helm chart"
  type        = string
  default     = "2.9.10"
}

# OpenTelemetry Variables
variable "opentelemetry_chart_version" {
  description = "Version of the OpenTelemetry Helm chart"
  type        = string
  default     = "0.55.0"
}

# Kubernetes Dashboard Variables
variable "kubernetes_dashboard_chart_version" {
  description = "Version of the Kubernetes Dashboard Helm chart"
  type        = string
  default     = "6.0.8"
}

# Alerting Variables
variable "slack_webhook_url" {
  description = "Slack webhook URL for alerting"
  type        = string
  sensitive   = true
  default     = ""
}

variable "pagerduty_service_key" {
  description = "PagerDuty service key for alerting"
  type        = string
  sensitive   = true
  default     = ""
}
