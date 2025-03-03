terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

# Local variables
locals {
  tags = merge(
    var.tags,
    {
      Name        = "${var.env}-${var.name}"
      Environment = var.env
      Terraform   = "true"
    }
  )
  
  parameter_group_name = var.create_parameter_group ? aws_elasticache_parameter_group.this[0].name : var.parameter_group_name
  subnet_group_name    = var.create_subnet_group ? aws_elasticache_subnet_group.this[0].name : var.subnet_group_name
}

# Subnet group
resource "aws_elasticache_subnet_group" "this" {
  count = var.create_subnet_group ? 1 : 0

  name        = "${var.env}-${var.name}-subnet-group"
  description = "Subnet group for ${var.name} ElastiCache Redis cluster"
  subnet_ids  = var.subnet_ids

  tags = local.tags
}

# Parameter group
resource "aws_elasticache_parameter_group" "this" {
  count = var.create_parameter_group ? 1 : 0

  name        = "${var.env}-${var.name}-param-group"
  description = "Parameter group for ${var.name} ElastiCache Redis cluster"
  family      = var.parameter_group_family

  dynamic "parameter" {
    for_each = var.parameter_group_parameters
    content {
      name  = parameter.key
      value = parameter.value
    }
  }

  tags = local.tags
}

# Security group
resource "aws_security_group" "this" {
  count = var.create_security_group ? 1 : 0

  name        = "${var.env}-${var.name}-sg"
  description = "Security group for ${var.name} ElastiCache Redis cluster"
  vpc_id      = var.vpc_id

  tags = local.tags
}

resource "aws_security_group_rule" "ingress_security_groups" {
  count = var.create_security_group ? length(var.allowed_security_group_ids) : 0

  type                     = "ingress"
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = var.allowed_security_group_ids[count.index]
  security_group_id        = aws_security_group.this[0].id
}

resource "aws_security_group_rule" "ingress_cidr_blocks" {
  count = var.create_security_group && length(var.allowed_cidr_blocks) > 0 ? 1 : 0

  type              = "ingress"
  from_port         = var.port
  to_port           = var.port
  protocol          = "tcp"
  cidr_blocks       = var.allowed_cidr_blocks
  security_group_id = aws_security_group.this[0].id
}

resource "aws_security_group_rule" "egress" {
  count = var.create_security_group ? 1 : 0

  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.this[0].id
}

# KMS key for encryption
resource "aws_kms_key" "this" {
  count = var.create_kms_key ? 1 : 0

  description             = "KMS key for ${var.name} ElastiCache Redis cluster"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.tags
}

resource "aws_kms_alias" "this" {
  count = var.create_kms_key ? 1 : 0

  name          = "alias/${var.env}-${var.name}-redis"
  target_key_id = aws_kms_key.this[0].key_id
}

# Redis replication group (cluster)
resource "aws_elasticache_replication_group" "this" {
  replication_group_id          = "${var.env}-${var.name}"
  description                   = "${var.env} ${var.name} Redis cluster"
  node_type                     = var.node_type
  port                          = var.port
  parameter_group_name          = local.parameter_group_name
  subnet_group_name             = local.subnet_group_name
  security_group_ids            = var.create_security_group ? [aws_security_group.this[0].id] : var.security_group_ids
  automatic_failover_enabled    = var.automatic_failover_enabled
  multi_az_enabled              = var.multi_az_enabled
  num_cache_clusters            = var.num_cache_clusters
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  kms_key_id                    = var.create_kms_key ? aws_kms_key.this[0].arn : var.kms_key_id
  auth_token                    = var.auth_token
  engine_version                = var.engine_version
  
  maintenance_window            = var.maintenance_window
  snapshot_window               = var.snapshot_window
  snapshot_retention_limit      = var.snapshot_retention_limit
  final_snapshot_identifier     = "${var.env}-${var.name}-final"
  auto_minor_version_upgrade    = var.auto_minor_version_upgrade
  apply_immediately             = var.apply_immediately
  
  # Redis configuration
  data_tiering_enabled          = var.data_tiering_enabled
  
  # Network
  preferred_cache_cluster_azs   = var.preferred_cache_cluster_azs
  
  # Monitoring
  notification_topic_arn        = var.notification_topic_arn
  
  # Serverless
  dynamic "serverless_cache_configuration" {
    for_each = var.serverless_enabled ? [1] : []
    content {
      max_cache_memory_usage_gb = var.serverless_max_cache_memory_usage_gb
      snapshot_retention_limit  = var.snapshot_retention_limit
    }
  }
  
  # Non-serverless configuration
  dynamic "log_delivery_configuration" {
    for_each = var.enable_log_delivery ? [1] : []
    content {
      destination      = var.log_delivery_destination
      destination_type = var.log_delivery_destination_type
      log_format       = var.log_delivery_format
      log_type         = var.log_delivery_type
    }
  }
  
  lifecycle {
    ignore_changes = [
      engine_version
    ]
  }
  
  tags = local.tags
}

# CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = var.create_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.env}-${var.name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Monitors high CPU utilization for ${var.name} ElastiCache Redis cluster"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.this.id
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "memory" {
  count = var.create_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.env}-${var.name}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Monitors high memory utilization for ${var.name} ElastiCache Redis cluster"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.this.id
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "connections" {
  count = var.create_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.env}-${var.name}-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = var.max_connections_threshold
  alarm_description   = "Monitors high connection count for ${var.name} ElastiCache Redis cluster"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.this.id
  }

  tags = local.tags
} 