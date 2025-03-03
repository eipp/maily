# Maily Monitoring Module

# Kubernetes namespace for monitoring
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    
    labels = {
      name        = "monitoring"
      environment = var.environment
    }
  }
}

# Prometheus Helm Release
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = var.prometheus_chart_version

  values = [
    templatefile("${path.module}/templates/prometheus-values.yaml", {
      retention_days      = var.prometheus_retention_days
      scrape_interval     = var.prometheus_scrape_interval
      grafana_version     = var.grafana_version
      grafana_admin_password = var.grafana_admin_password
      environment         = var.environment
      domain              = var.domain
    })
  ]

  set {
    name  = "grafana.adminPassword"
    value = var.grafana_admin_password
  }

  set {
    name  = "prometheus.prometheusSpec.retention"
    value = "${var.prometheus_retention_days}d"
  }

  set {
    name  = "prometheus.prometheusSpec.scrapeInterval"
    value = "${var.prometheus_scrape_interval}s"
  }

  set {
    name  = "grafana.image.tag"
    value = var.grafana_version
  }
}

# Datadog Helm Release
resource "helm_release" "datadog" {
  name       = "datadog"
  repository = "https://helm.datadoghq.com"
  chart      = "datadog"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = var.datadog_chart_version

  values = [
    templatefile("${path.module}/templates/datadog-values.yaml", {
      datadog_api_key = var.datadog_api_key
      datadog_app_key = var.datadog_app_key
      environment     = var.environment
      domain          = var.domain
    })
  ]

  set {
    name  = "datadog.apiKey"
    value = var.datadog_api_key
  }

  set {
    name  = "datadog.appKey"
    value = var.datadog_app_key
  }

  set {
    name  = "datadog.logs.enabled"
    value = "true"
  }

  set {
    name  = "datadog.logs.containerCollectAll"
    value = "true"
  }

  set {
    name  = "datadog.apm.enabled"
    value = "true"
  }

  set {
    name  = "datadog.processAgent.enabled"
    value = "true"
  }

  set {
    name  = "datadog.networkMonitoring.enabled"
    value = "true"
  }

  set {
    name  = "datadog.tags"
    value = "env:${var.environment}"
  }
}

# Loki Helm Release for log aggregation
resource "helm_release" "loki" {
  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = var.loki_chart_version

  values = [
    templatefile("${path.module}/templates/loki-values.yaml", {
      environment = var.environment
      domain      = var.domain
    })
  ]

  set {
    name  = "grafana.enabled"
    value = "false"  # We're using Grafana from Prometheus stack
  }

  set {
    name  = "loki.persistence.enabled"
    value = "true"
  }

  set {
    name  = "loki.persistence.size"
    value = "50Gi"
  }

  set {
    name  = "promtail.enabled"
    value = "true"
  }
}

# OpenTelemetry Collector for distributed tracing
resource "helm_release" "opentelemetry" {
  name       = "opentelemetry"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = var.opentelemetry_chart_version

  values = [
    templatefile("${path.module}/templates/opentelemetry-values.yaml", {
      environment = var.environment
      domain      = var.domain
    })
  ]
}

# Kubernetes Dashboard
resource "helm_release" "kubernetes_dashboard" {
  name       = "kubernetes-dashboard"
  repository = "https://kubernetes.github.io/dashboard/"
  chart      = "kubernetes-dashboard"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = var.kubernetes_dashboard_chart_version

  values = [
    templatefile("${path.module}/templates/kubernetes-dashboard-values.yaml", {
      environment = var.environment
      domain      = var.domain
    })
  ]

  set {
    name  = "protocolHttp"
    value = "true"
  }

  set {
    name  = "service.externalPort"
    value = "80"
  }

  set {
    name  = "metricsScraper.enabled"
    value = "true"
  }
}

# Custom Maily Dashboards for Grafana
resource "kubernetes_config_map" "grafana_dashboards" {
  metadata {
    name      = "maily-grafana-dashboards"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "maily-overview.json"      = file("${path.module}/dashboards/maily-overview.json")
    "maily-ai-services.json"   = file("${path.module}/dashboards/maily-ai-services.json")
    "maily-websocket.json"     = file("${path.module}/dashboards/maily-websocket.json")
    "maily-blockchain.json"    = file("${path.module}/dashboards/maily-blockchain.json")
  }

  depends_on = [
    helm_release.prometheus
  ]
}

# Alert Manager Configuration
resource "kubernetes_config_map" "alertmanager_config" {
  metadata {
    name      = "alertmanager-config"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }

  data = {
    "alertmanager.yml" = templatefile("${path.module}/templates/alertmanager.yml", {
      slack_webhook_url = var.slack_webhook_url
      pagerduty_service_key = var.pagerduty_service_key
      environment = var.environment
    })
  }

  depends_on = [
    helm_release.prometheus
  ]
}

# Prometheus Rules for Maily-specific alerts
resource "kubernetes_config_map" "prometheus_rules" {
  metadata {
    name      = "maily-prometheus-rules"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    
    labels = {
      prometheus_rule = "true"
    }
  }

  data = {
    "maily-alerts.yml" = file("${path.module}/rules/maily-alerts.yml")
  }

  depends_on = [
    helm_release.prometheus
  ]
}
