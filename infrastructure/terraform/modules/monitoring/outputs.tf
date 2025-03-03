# Maily Monitoring Module Outputs

output "prometheus_namespace" {
  description = "The namespace where Prometheus is deployed"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "prometheus_service_name" {
  description = "The service name for Prometheus"
  value       = "prometheus-operated"
}

output "grafana_service_name" {
  description = "The service name for Grafana"
  value       = "prometheus-grafana"
}

output "alertmanager_service_name" {
  description = "The service name for Alertmanager"
  value       = "alertmanager-operated"
}

output "datadog_service_name" {
  description = "The service name for Datadog"
  value       = "datadog"
}

output "loki_service_name" {
  description = "The service name for Loki"
  value       = "loki"
}

output "opentelemetry_service_name" {
  description = "The service name for OpenTelemetry Collector"
  value       = "opentelemetry-collector"
}

output "kubernetes_dashboard_service_name" {
  description = "The service name for Kubernetes Dashboard"
  value       = "kubernetes-dashboard"
}

output "grafana_admin_password" {
  description = "The admin password for Grafana"
  value       = var.grafana_admin_password
  sensitive   = true
}

output "prometheus_url" {
  description = "The URL for Prometheus"
  value       = "https://prometheus.${var.domain}"
}

output "grafana_url" {
  description = "The URL for Grafana"
  value       = "https://grafana.${var.domain}"
}

output "alertmanager_url" {
  description = "The URL for Alertmanager"
  value       = "https://alertmanager.${var.domain}"
}

output "kubernetes_dashboard_url" {
  description = "The URL for Kubernetes Dashboard"
  value       = "https://k8s-dashboard.${var.domain}"
}

output "datadog_dashboard_url" {
  description = "The URL for Datadog Dashboard"
  value       = "https://app.datadoghq.com/dashboard/lists"
}
