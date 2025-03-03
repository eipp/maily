/**
 * VPC Peering Configuration for Database Access
 *
 * This Terraform configuration sets up VPC peering between the Kubernetes cluster VPC
 * and the database VPC to enable secure database access.
 */

# VPC Peering Connection
resource "aws_vpc_peering_connection" "cluster_to_db" {
  vpc_id        = var.cluster_vpc_id
  peer_vpc_id   = var.database_vpc_id
  auto_accept   = var.same_account_peering

  tags = merge(
    var.common_tags,
    {
      Name = "maily-cluster-to-db-peering"
      Environment = var.environment
    }
  )
}

# Accept VPC peering request (for cross-account peering)
resource "aws_vpc_peering_connection_accepter" "db_accepter" {
  count                     = var.same_account_peering ? 0 : 1
  vpc_peering_connection_id = aws_vpc_peering_connection.cluster_to_db.id
  auto_accept               = true

  tags = merge(
    var.common_tags,
    {
      Name = "maily-db-peering-accepter"
      Environment = var.environment
    }
  )
}

# Route tables for cluster VPC to database VPC
resource "aws_route" "cluster_to_db" {
  count                     = length(var.cluster_route_table_ids)
  route_table_id            = var.cluster_route_table_ids[count.index]
  destination_cidr_block    = var.database_vpc_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.cluster_to_db.id
}

# Route tables for database VPC to cluster VPC
resource "aws_route" "db_to_cluster" {
  count                     = length(var.database_route_table_ids)
  route_table_id            = var.database_route_table_ids[count.index]
  destination_cidr_block    = var.cluster_vpc_cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.cluster_to_db.id
}

# Security group for database access
resource "aws_security_group" "db_access" {
  name        = "maily-db-access-${var.environment}"
  description = "Security group for database access from Kubernetes cluster"
  vpc_id      = var.database_vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.cluster_vpc_cidr]
    description = "PostgreSQL access from Kubernetes cluster"
  }

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.cluster_vpc_cidr]
    description = "Redis access from Kubernetes cluster"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    var.common_tags,
    {
      Name = "maily-db-access-${var.environment}"
      Environment = var.environment
    }
  )
}

# DNS resolution support for VPC peering
resource "aws_vpc_peering_connection_options" "cluster_to_db_options" {
  vpc_peering_connection_id = aws_vpc_peering_connection.cluster_to_db.id

  accepter {
    allow_remote_vpc_dns_resolution = true
  }

  requester {
    allow_remote_vpc_dns_resolution = true
  }

  depends_on = [
    aws_vpc_peering_connection_accepter.db_accepter
  ]
}

# Output the VPC peering connection ID
output "vpc_peering_connection_id" {
  description = "The ID of the VPC peering connection"
  value       = aws_vpc_peering_connection.cluster_to_db.id
}

# Output the database security group ID
output "db_security_group_id" {
  description = "The ID of the database security group"
  value       = aws_security_group.db_access.id
}
