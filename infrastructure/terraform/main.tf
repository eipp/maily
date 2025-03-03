# Maily Infrastructure Terraform Configuration

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 0.15"
    }
  }

  backend "s3" {
    bucket         = "maily-terraform-state"
    key            = "maily/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "maily-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Maily"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubernetes_config_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubernetes_config_path
  }
}

provider "vercel" {
  api_token = var.vercel_token
  team      = var.vercel_team_id
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"

  cluster_name    = "maily-${var.environment}"
  cluster_version = var.kubernetes_version
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  node_groups = {
    standard = {
      name           = "standard"
      instance_types = [var.standard_instance_type]
      min_size       = var.standard_min_size
      max_size       = var.standard_max_size
      desired_size   = var.standard_min_size
    }
    ai_services = {
      name           = "ai-services"
      instance_types = [var.ai_services_instance_type]
      min_size       = var.ai_services_min_size
      max_size       = var.ai_services_max_size
      desired_size   = var.ai_services_min_size
    }
    websocket = {
      name           = "websocket"
      instance_types = [var.websocket_instance_type]
      min_size       = var.websocket_min_size
      max_size       = var.websocket_max_size
      desired_size   = var.websocket_min_size
    }
  }

  tags = {
    Environment = var.environment
  }
}

# VPC
module "vpc" {
  source = "./modules/vpc"

  name = "maily-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway = true
  single_nat_gateway = var.environment != "production"

  tags = {
    Environment = var.environment
  }
}

# RDS (PostgreSQL)
module "rds" {
  source = "./modules/rds"

  identifier        = "maily-${var.environment}"
  engine            = "postgres"
  engine_version    = var.postgres_version
  instance_class    = var.database_instance_class
  allocated_storage = var.database_storage_gb
  storage_encrypted = true

  name     = "maily"
  username = "maily"
  password = var.database_password

  vpc_security_group_ids = [module.security_groups.database_sg_id]
  subnet_ids             = module.vpc.database_subnets

  backup_retention_period = var.database_backup_retention_days
  multi_az                = var.database_multi_az

  tags = {
    Environment = var.environment
  }
}

# ElastiCache (Redis)
module "redis" {
  source = "./modules/redis"

  cluster_id           = "maily-${var.environment}"
  engine_version       = var.redis_version
  node_type            = var.redis_instance_type
  num_cache_clusters   = var.redis_replicas_per_shard
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [module.security_groups.redis_sg_id]

  tags = {
    Environment = var.environment
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "maily-${var.environment}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# S3 Buckets
module "s3_buckets" {
  source = "./modules/s3"

  buckets = {
    assets = {
      name = "maily-${var.environment}-assets"
      cors_enabled = true
    }
    uploads = {
      name = "maily-${var.environment}-uploads"
      cors_enabled = true
    }
    backups = {
      name = "maily-${var.environment}-backups"
      cors_enabled = false
    }
  }

  tags = {
    Environment = var.environment
  }
}

# Security Groups
module "security_groups" {
  source = "./modules/security_groups"

  vpc_id      = module.vpc.vpc_id
  environment = var.environment

  tags = {
    Environment = var.environment
  }
}

# Kubernetes Resources
module "kubernetes_resources" {
  source = "./modules/kubernetes"

  environment = var.environment
  domain      = var.domain

  depends_on = [module.eks]
}

# Vercel Project
module "vercel" {
  source = "./modules/vercel"

  project_name = "maily-${var.environment}"
  framework    = "nextjs"
  environment  = var.environment
  domain       = var.domain

  environment_variables = {
    NEXT_PUBLIC_API_URL       = "https://api.${var.domain}"
    NEXT_PUBLIC_WEBSOCKET_URL = "wss://ws.${var.domain}"
    NEXT_PUBLIC_SUPABASE_URL  = var.supabase_url
    NEXT_PUBLIC_SUPABASE_ANON_KEY = var.supabase_anon_key
  }
}

# Monitoring Resources
module "monitoring" {
  source = "./modules/monitoring"

  environment = var.environment
  domain      = var.domain

  datadog_api_key = var.datadog_api_key
  datadog_app_key = var.datadog_app_key

  prometheus_retention_days      = var.prometheus_retention_days
  prometheus_scrape_interval     = var.prometheus_scrape_interval
  grafana_version                = var.grafana_version
  grafana_admin_password         = var.grafana_admin_password

  depends_on = [module.eks]
}

# Vault for Secrets Management
module "vault" {
  source = "./modules/vault"

  environment = var.environment
  domain      = var.domain
  
  vault_version = var.vault_version

  depends_on = [module.eks]
}
