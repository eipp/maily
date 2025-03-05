terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12.0"
    }
  }
}

# The providers will be passed from the root module
# instead of being configured locally

# Create the maily-production namespace
resource "kubernetes_namespace" "maily_production" {
  metadata {
    name = "maily-production"
    labels = {
      environment = "production"
      managed-by  = "terraform"
    }
  }
}

# Deploy cert-manager for TLS certificate management
resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  create_namespace = true
  version    = var.cert_manager_version

  set {
    name  = "installCRDs"
    value = "true"
  }

  set {
    name  = "global.leaderElection.namespace"
    value = "cert-manager"
  }
}

# Deploy nginx-ingress controller
resource "helm_release" "nginx_ingress" {
  name       = "nginx-ingress"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "ingress-nginx"
  create_namespace = true
  version    = var.nginx_ingress_version

  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }

  set {
    name  = "controller.metrics.enabled"
    value = "true"
  }

  set {
    name  = "controller.metrics.serviceMonitor.enabled"
    value = "true"
  }

  depends_on = [kubernetes_namespace.maily_production]
}

# Deploy Prometheus and Grafana for monitoring
resource "helm_release" "prometheus_stack" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = "monitoring"
  create_namespace = true
  version    = var.prometheus_version

  values = [
    file("${path.module}/prometheus-values.yaml")
  ]

  depends_on = [helm_release.nginx_ingress]
}

# Deploy HorizontalPodAutoscaler for email-processing-service
resource "kubernetes_manifest" "email_processing_hpa" {
  manifest = {
    apiVersion = "autoscaling/v2"
    kind       = "HorizontalPodAutoscaler"
    metadata = {
      name      = "email-processing-service"
      namespace = kubernetes_namespace.maily_production.metadata[0].name
    }
    spec = {
      scaleTargetRef = {
        apiVersion = "apps/v1"
        kind       = "Deployment"
        name       = "email-processing-service"
      }
      minReplicas = 3
      maxReplicas = 10
      metrics = [
        {
          type = "Resource"
          resource = {
            name = "cpu"
            target = {
              type               = "Utilization"
              averageUtilization = 70
            }
          }
        }
      ]
    }
  }

  depends_on = [kubernetes_namespace.maily_production]
}
