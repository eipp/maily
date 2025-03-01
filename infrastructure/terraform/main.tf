terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket = "maily-terraform-state"
    key    = "state/terraform.tfstate"
    region = "us-east-1"
    dynamodb_table = "maily-terraform-locks"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Network Configuration
module "vpc" {
  source = "./modules/vpc"

  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  azs         = var.availability_zones
}

# Security Groups
module "security_groups" {
  source = "./modules/security"

  vpc_id      = module.vpc.vpc_id
  environment = var.environment
}

# ECS Cluster and Services
module "ecs" {
  source = "./modules/ecs"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets

  frontend_image = var.frontend_image
  backend_image  = var.backend_image

  frontend_cpu    = var.frontend_cpu
  frontend_memory = var.frontend_memory
  backend_cpu     = var.backend_cpu
  backend_memory  = var.backend_memory

  security_groups = module.security_groups.ecs_security_group_ids
}

# RDS Database
module "rds" {
  source = "./modules/rds"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password

  security_groups = [module.security_groups.rds_security_group_id]
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets

  redis_node_type = var.redis_node_type
  security_groups = [module.security_groups.redis_security_group_id]
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"

  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets

  security_groups = [module.security_groups.alb_security_group_id]
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"

  environment = var.environment
  bucket_name = var.s3_bucket_name
}

# CDN for Static Assets
module "cdn" {
  source = "./modules/cdn"

  project_name       = "maily"
  environment        = var.environment
  custom_domain      = var.cdn_custom_domain
  acm_certificate_arn = var.cdn_certificate_arn
}
