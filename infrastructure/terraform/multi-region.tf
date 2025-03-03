/**
 * Multi-Region Support
 *
 * This Terraform configuration sets up multi-region support for the JustMaily platform,
 * including cross-region replication, global load balancing, and disaster recovery.
 */

# Provider configuration for primary region
provider "aws" {
  alias  = "primary"
  region = var.primary_region
}

# Provider configuration for secondary region
provider "aws" {
  alias  = "secondary"
  region = var.secondary_region
}

# S3 bucket for cross-region replication in primary region
resource "aws_s3_bucket" "primary_replication" {
  provider = aws.primary
  bucket   = "maily-replication-${var.environment}-${var.primary_region}"
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-replication-${var.environment}-${var.primary_region}"
      Environment = var.environment
      Region = var.primary_region
    }
  )
}

# S3 bucket for cross-region replication in secondary region
resource "aws_s3_bucket" "secondary_replication" {
  provider = aws.secondary
  bucket   = "maily-replication-${var.environment}-${var.secondary_region}"
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-replication-${var.environment}-${var.secondary_region}"
      Environment = var.environment
      Region = var.secondary_region
    }
  )
}

# S3 bucket versioning for primary region
resource "aws_s3_bucket_versioning" "primary_versioning" {
  provider = aws.primary
  bucket   = aws_s3_bucket.primary_replication.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket versioning for secondary region
resource "aws_s3_bucket_versioning" "secondary_versioning" {
  provider = aws.secondary
  bucket   = aws_s3_bucket.secondary_replication.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for S3 replication
resource "aws_iam_role" "replication" {
  provider = aws.primary
  name     = "maily-s3-replication-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-s3-replication-${var.environment}"
      Environment = var.environment
    }
  )
}

# IAM policy for S3 replication
resource "aws_iam_policy" "replication" {
  provider    = aws.primary
  name        = "maily-s3-replication-policy-${var.environment}"
  description = "Policy for S3 cross-region replication"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.primary_replication.arn
        ]
      },
      {
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.primary_replication.arn}/*"
        ]
      },
      {
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.secondary_replication.arn}/*"
        ]
      }
    ]
  })
}

# Attach policy to IAM role
resource "aws_iam_role_policy_attachment" "replication" {
  provider   = aws.primary
  role       = aws_iam_role.replication.name
  policy_arn = aws_iam_policy.replication.arn
}

# S3 bucket replication configuration
resource "aws_s3_bucket_replication_configuration" "replication" {
  provider = aws.primary
  
  # Must have bucket versioning enabled first
  depends_on = [aws_s3_bucket_versioning.primary_versioning]
  
  role   = aws_iam_role.replication.arn
  bucket = aws_s3_bucket.primary_replication.id
  
  rule {
    id     = "maily-replication-rule"
    status = "Enabled"
    
    destination {
      bucket        = aws_s3_bucket.secondary_replication.arn
      storage_class = "STANDARD"
    }
  }
}

# DynamoDB global table
resource "aws_dynamodb_table" "global" {
  provider     = aws.primary
  name         = "maily-global-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Id"
  
  attribute {
    name = "Id"
    type = "S"
  }
  
  replica {
    region_name = var.secondary_region
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-global-${var.environment}"
      Environment = var.environment
    }
  )
}

# Route53 health check for primary region
resource "aws_route53_health_check" "primary" {
  provider          = aws.primary
  fqdn              = "api.${var.primary_region}.${var.domain_name}"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-primary-health-check-${var.environment}"
      Environment = var.environment
      Region = var.primary_region
    }
  )
}

# Route53 health check for secondary region
resource "aws_route53_health_check" "secondary" {
  provider          = aws.primary
  fqdn              = "api.${var.secondary_region}.${var.domain_name}"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-secondary-health-check-${var.environment}"
      Environment = var.environment
      Region = var.secondary_region
    }
  )
}

# Route53 DNS records for global endpoint
resource "aws_route53_record" "global" {
  provider = aws.primary
  zone_id  = var.route53_zone_id
  name     = "api.${var.domain_name}"
  type     = "CNAME"
  ttl      = 60
  
  failover_routing_policy {
    type = "PRIMARY"
  }
  
  set_identifier = "primary"
  health_check_id = aws_route53_health_check.primary.id
  records = ["api.${var.primary_region}.${var.domain_name}"]
}

resource "aws_route53_record" "global_secondary" {
  provider = aws.primary
  zone_id  = var.route53_zone_id
  name     = "api.${var.domain_name}"
  type     = "CNAME"
  ttl      = 60
  
  failover_routing_policy {
    type = "SECONDARY"
  }
  
  set_identifier = "secondary"
  health_check_id = aws_route53_health_check.secondary.id
  records = ["api.${var.secondary_region}.${var.domain_name}"]
}

# CloudFront distribution for global content delivery
resource "aws_cloudfront_distribution" "global" {
  provider = aws.primary
  enabled  = true
  
  aliases = ["cdn.${var.domain_name}"]
  
  origin {
    domain_name = "cdn.${var.primary_region}.${var.domain_name}"
    origin_id   = "primary"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  origin {
    domain_name = "cdn.${var.secondary_region}.${var.domain_name}"
    origin_id   = "secondary"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  origin_group {
    origin_id = "failover-group"
    
    failover_criteria {
      status_codes = [500, 502, 503, 504]
    }
    
    member {
      origin_id = "primary"
    }
    
    member {
      origin_id = "secondary"
    }
  }
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "failover-group"
    
    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = var.cloudfront_certificate_arn
    ssl_support_method  = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-cdn-${var.environment}"
      Environment = var.environment
    }
  )
}

# RDS read replica in secondary region
resource "aws_db_instance" "read_replica" {
  provider                = aws.secondary
  identifier              = "maily-db-replica-${var.environment}"
  replicate_source_db     = var.primary_db_arn
  instance_class          = var.db_instance_class
  publicly_accessible     = false
  skip_final_snapshot     = true
  backup_retention_period = 7
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-db-replica-${var.environment}"
      Environment = var.environment
      Region = var.secondary_region
    }
  )
}

# ElastiCache Global Datastore
resource "aws_elasticache_global_replication_group" "redis" {
  provider                           = aws.primary
  global_replication_group_id_suffix = "maily-${var.environment}"
  primary_replication_group_id       = var.primary_redis_replication_group_id
}

resource "aws_elasticache_replication_group" "secondary" {
  provider                   = aws.secondary
  replication_group_id       = "maily-redis-${var.environment}-${var.secondary_region}"
  description                = "Maily Redis secondary replication group"
  global_replication_group_id = aws_elasticache_global_replication_group.redis.id
  automatic_failover_enabled = true
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-redis-${var.environment}-${var.secondary_region}"
      Environment = var.environment
      Region = var.secondary_region
    }
  )
}

# Output the global endpoint
output "global_api_endpoint" {
  description = "The global API endpoint"
  value       = "api.${var.domain_name}"
}

# Output the CloudFront distribution domain name
output "cloudfront_domain_name" {
  description = "The CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.global.domain_name
}

# Output the DynamoDB global table name
output "dynamodb_global_table_name" {
  description = "The DynamoDB global table name"
  value       = aws_dynamodb_table.global.name
}

# Output the RDS read replica endpoint
output "rds_read_replica_endpoint" {
  description = "The RDS read replica endpoint"
  value       = aws_db_instance.read_replica.endpoint
}

# Output the ElastiCache secondary endpoint
output "elasticache_secondary_endpoint" {
  description = "The ElastiCache secondary endpoint"
  value       = aws_elasticache_replication_group.secondary.configuration_endpoint_address
}
