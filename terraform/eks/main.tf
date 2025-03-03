/**
 * # Maily EKS Cluster Deployment
 *
 * This Terraform configuration deploys an Amazon EKS cluster for the Maily application.
 */

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Use data sources to get VPC and subnet information
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-${var.environment}-vpc"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-${var.environment}-private-*"]
  }
}

data "aws_subnet" "private" {
  for_each = toset(data.aws_subnets.private.ids)
  id       = each.value
}

locals {
  private_subnet_ids         = data.aws_subnets.private.ids
  private_subnet_cidr_blocks = [for s in data.aws_subnet.private : s.cidr_block]
}

# Create EKS cluster using the module
module "eks" {
  source = "../modules/eks"

  project_name             = var.project_name
  environment              = var.environment
  vpc_id                   = data.aws_vpc.main.id
  subnet_ids               = local.private_subnet_ids
  private_subnet_cidr_blocks = local.private_subnet_cidr_blocks
  kubernetes_version       = var.kubernetes_version
  
  # Node groups configuration
  node_groups = {
    general = {
      desired_size   = var.general_node_group_desired_size
      max_size       = var.general_node_group_max_size
      min_size       = var.general_node_group_min_size
      instance_types = var.general_node_group_instance_types
      capacity_type  = "ON_DEMAND"
      disk_size      = 20
      labels = {
        "role" = "general"
      }
    },
    
    services = {
      desired_size   = var.services_node_group_desired_size
      max_size       = var.services_node_group_max_size
      min_size       = var.services_node_group_min_size
      instance_types = var.services_node_group_instance_types
      capacity_type  = "ON_DEMAND"
      disk_size      = 30
      labels = {
        "role" = "services"
      }
    }
  }
  
  # Endpoint access configuration
  endpoint_private_access = var.endpoint_private_access
  endpoint_public_access  = var.endpoint_public_access
  public_access_cidrs     = var.public_access_cidrs
  
  # Logging configuration
  enabled_cluster_log_types = var.enabled_cluster_log_types
  log_retention_days        = var.log_retention_days
  
  # Tags
  tags = var.tags
}

# Save kubeconfig to a local file
resource "local_file" "kubeconfig" {
  content  = module.eks.kubeconfig
  filename = "${path.module}/kubeconfig"
}
