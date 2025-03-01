terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "maily-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "maily-terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
  default_tags {
    tags = {
      Environment = "production"
      Project     = "maily"
      ManagedBy   = "terraform"
    }
  }
}

# Use data sources to fetch EKS cluster information
data "aws_eks_cluster" "production" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "production" {
  name = var.cluster_name
}

# Use VPC module to create networking infrastructure
module "vpc" {
  source = "../../modules/vpc"

  environment      = "production"
  vpc_cidr         = "10.0.0.0/16"
  azs              = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets   = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = false  # For high availability in production
}

# Deploy Kubernetes infrastructure
module "kubernetes" {
  source = "../../modules/kubernetes"

  cluster_endpoint        = data.aws_eks_cluster.production.endpoint
  cluster_ca_certificate  = data.aws_eks_cluster.production.certificate_authority[0].data
  kubernetes_token        = data.aws_eks_cluster_auth.production.token

  cert_manager_version    = "v1.13.1"
  nginx_ingress_version   = "4.8.3"
  prometheus_version      = "54.2.2"
}

# Configure Vault for secret management
module "vault" {
  source = "../../modules/vault"

  environment      = "production"
  vpc_id           = module.vpc.vpc_id
  private_subnets  = module.vpc.private_subnets
  instance_type    = "t3.medium"  # Adjust based on workload
  key_name         = var.key_name
}

# Create IAM permissions for services
resource "aws_iam_role" "eks_service_role" {
  name = "eks-service-role-production"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

# Configure CDN for assets
module "cdn" {
  source = "../../modules/cdn"

  environment     = "production"
  project_name    = "maily"
  custom_domain   = "assets.justmaily.com"
  certificate_arn = var.certificate_arn
}

# Configure CDN for media
module "media_cdn" {
  source = "../../modules/cdn"

  environment     = "production"
  project_name    = "maily"
  custom_domain   = "media.justmaily.com"
  certificate_arn = var.certificate_arn
  cache_behaviors = ["*.jpg", "*.png", "*.gif", "*.mp4", "*.webp", "*.svg"]
}

# Configure global accelerator for global traffic routing
module "global_accelerator" {
  source = "../../modules/global-accelerator"

  name            = "maily-production"
  enable_stickiness = true
  endpoint_arns   = [module.kubernetes.load_balancer_arn]
}

# Output important information
output "kubernetes_cluster_endpoint" {
  value = data.aws_eks_cluster.production.endpoint
}

output "assets_cdn_domain_name" {
  value = module.cdn.domain_name
}

output "media_cdn_domain_name" {
  value = module.media_cdn.domain_name
}

output "global_accelerator_dns_name" {
  value = module.global_accelerator.dns_name
}
