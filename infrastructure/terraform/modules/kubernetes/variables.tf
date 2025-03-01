variable "cluster_endpoint" {
  description = "The endpoint for the Kubernetes API server"
  type        = string
}

variable "cluster_ca_certificate" {
  description = "The base64 encoded CA certificate for the Kubernetes cluster"
  type        = string
  sensitive   = true
}

variable "kubernetes_token" {
  description = "The token used to authenticate with the Kubernetes API"
  type        = string
  sensitive   = true
}

variable "cert_manager_version" {
  description = "The version of cert-manager to deploy"
  type        = string
  default     = "v1.13.1"
}

variable "nginx_ingress_version" {
  description = "The version of nginx-ingress to deploy"
  type        = string
  default     = "4.8.3"
}

variable "prometheus_version" {
  description = "The version of prometheus-operator to deploy"
  type        = string
  default     = "54.2.2"
}
