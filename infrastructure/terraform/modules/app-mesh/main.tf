provider "aws" {
  region = var.primary_region
}

provider "aws" {
  alias  = "secondary"
  region = var.secondary_region
}

# Create App Mesh service mesh
resource "aws_appmesh_mesh" "maily_mesh" {
  name = var.mesh_name

  spec {
    egress_filter {
      type = "ALLOW_ALL"
    }
  }

  tags = {
    Name        = var.mesh_name
    Environment = var.environment
  }
}

# Create virtual nodes for each service in the primary region
resource "aws_appmesh_virtual_node" "primary_api" {
  name      = "api-node-primary"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    listener {
      port_mapping {
        port     = 8000
        protocol = "http"
      }

      health_check {
        protocol            = "http"
        path                = "/health"
        healthy_threshold   = 2
        unhealthy_threshold = 2
        timeout_millis      = 2000
        interval_millis     = 5000
      }
    }

    service_discovery {
      dns {
        hostname = "api.${var.primary_region}.${var.domain_name}"
      }
    }

    backend {
      virtual_service {
        virtual_service_name = "database.${var.mesh_name}.local"
      }
    }

    backend {
      virtual_service {
        virtual_service_name = "redis.${var.mesh_name}.local"
      }
    }

    logging {
      access_log {
        file {
          path = "/dev/stdout"
        }
      }
    }
  }

  tags = {
    Name        = "api-node-primary"
    Environment = var.environment
    Region      = var.primary_region
  }
}

resource "aws_appmesh_virtual_node" "primary_web" {
  name      = "web-node-primary"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    listener {
      port_mapping {
        port     = 3000
        protocol = "http"
      }

      health_check {
        protocol            = "http"
        path                = "/api/health"
        healthy_threshold   = 2
        unhealthy_threshold = 2
        timeout_millis      = 2000
        interval_millis     = 5000
      }
    }

    service_discovery {
      dns {
        hostname = "web.${var.primary_region}.${var.domain_name}"
      }
    }

    backend {
      virtual_service {
        virtual_service_name = "api.${var.mesh_name}.local"
      }
    }

    logging {
      access_log {
        file {
          path = "/dev/stdout"
        }
      }
    }
  }

  tags = {
    Name        = "web-node-primary"
    Environment = var.environment
    Region      = var.primary_region
  }
}

# Create virtual nodes for each service in the secondary region
resource "aws_appmesh_virtual_node" "secondary_api" {
  provider  = aws.secondary
  name      = "api-node-secondary"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    listener {
      port_mapping {
        port     = 8000
        protocol = "http"
      }

      health_check {
        protocol            = "http"
        path                = "/health"
        healthy_threshold   = 2
        unhealthy_threshold = 2
        timeout_millis      = 2000
        interval_millis     = 5000
      }
    }

    service_discovery {
      dns {
        hostname = "api.${var.secondary_region}.${var.domain_name}"
      }
    }

    backend {
      virtual_service {
        virtual_service_name = "database.${var.mesh_name}.local"
      }
    }

    backend {
      virtual_service {
        virtual_service_name = "redis.${var.mesh_name}.local"
      }
    }

    logging {
      access_log {
        file {
          path = "/dev/stdout"
        }
      }
    }
  }

  tags = {
    Name        = "api-node-secondary"
    Environment = var.environment
    Region      = var.secondary_region
  }
}

resource "aws_appmesh_virtual_node" "secondary_web" {
  provider  = aws.secondary
  name      = "web-node-secondary"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    listener {
      port_mapping {
        port     = 3000
        protocol = "http"
      }

      health_check {
        protocol            = "http"
        path                = "/api/health"
        healthy_threshold   = 2
        unhealthy_threshold = 2
        timeout_millis      = 2000
        interval_millis     = 5000
      }
    }

    service_discovery {
      dns {
        hostname = "web.${var.secondary_region}.${var.domain_name}"
      }
    }

    backend {
      virtual_service {
        virtual_service_name = "api.${var.mesh_name}.local"
      }
    }

    logging {
      access_log {
        file {
          path = "/dev/stdout"
        }
      }
    }
  }

  tags = {
    Name        = "web-node-secondary"
    Environment = var.environment
    Region      = var.secondary_region
  }
}

# Create virtual services
resource "aws_appmesh_virtual_service" "api" {
  name      = "api.${var.mesh_name}.local"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    provider {
      virtual_router {
        virtual_router_name = aws_appmesh_virtual_router.api_router.name
      }
    }
  }

  tags = {
    Name        = "api-service"
    Environment = var.environment
  }
}

resource "aws_appmesh_virtual_service" "web" {
  name      = "web.${var.mesh_name}.local"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    provider {
      virtual_router {
        virtual_router_name = aws_appmesh_virtual_router.web_router.name
      }
    }
  }

  tags = {
    Name        = "web-service"
    Environment = var.environment
  }
}

# Create virtual routers
resource "aws_appmesh_virtual_router" "api_router" {
  name      = "api-router"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    listener {
      port_mapping {
        port     = 8000
        protocol = "http"
      }
    }
  }

  tags = {
    Name        = "api-router"
    Environment = var.environment
  }
}

resource "aws_appmesh_virtual_router" "web_router" {
  name      = "web-router"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  spec {
    listener {
      port_mapping {
        port     = 3000
        protocol = "http"
      }
    }
  }

  tags = {
    Name        = "web-router"
    Environment = var.environment
  }
}

# Create routes with weighted targets for multi-region routing
resource "aws_appmesh_route" "api_route" {
  name      = "api-route"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  virtual_router_name = aws_appmesh_virtual_router.api_router.name

  spec {
    http_route {
      match {
        prefix = "/"
      }

      action {
        weighted_target {
          virtual_node = aws_appmesh_virtual_node.primary_api.name
          weight       = var.primary_weight
        }

        weighted_target {
          virtual_node = aws_appmesh_virtual_node.secondary_api.name
          weight       = var.secondary_weight
        }
      }

      retry_policy {
        http_retry_events = ["server-error", "gateway-error", "client-error", "stream-error"]

        max_retries = 3

        per_retry_timeout {
          unit  = "ms"
          value = 2000
        }
      }
    }
  }

  tags = {
    Name        = "api-route"
    Environment = var.environment
  }
}

resource "aws_appmesh_route" "web_route" {
  name      = "web-route"
  mesh_name = aws_appmesh_mesh.maily_mesh.id

  virtual_router_name = aws_appmesh_virtual_router.web_router.name

  spec {
    http_route {
      match {
        prefix = "/"
      }

      action {
        weighted_target {
          virtual_node = aws_appmesh_virtual_node.primary_web.name
          weight       = var.primary_weight
        }

        weighted_target {
          virtual_node = aws_appmesh_virtual_node.secondary_web.name
          weight       = var.secondary_weight
        }
      }

      retry_policy {
        http_retry_events = ["server-error", "gateway-error", "client-error", "stream-error"]

        max_retries = 3

        per_retry_timeout {
          unit  = "ms"
          value = 2000
        }
      }
    }
  }

  tags = {
    Name        = "web-route"
    Environment = var.environment
  }
}
