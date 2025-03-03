terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
  }
}

# Local variables
locals {
  tags = merge(
    var.tags,
    {
      Name        = "${var.env}-${var.identifier}"
      Environment = var.env
      Terraform   = "true"
    }
  )
  
  parameter_group_name = var.create_parameter_group ? aws_db_parameter_group.this[0].name : var.parameter_group_name
  subnet_group_name    = var.create_subnet_group ? aws_db_subnet_group.this[0].name : var.subnet_group_name
  option_group_name    = var.create_option_group ? aws_db_option_group.this[0].name : var.option_group_name
}

# Random password if needed
resource "random_password" "master_password" {
  count   = var.create_random_password ? 1 : 0
  length  = 16
  special = false
}

# DB subnet group
resource "aws_db_subnet_group" "this" {
  count = var.create_subnet_group ? 1 : 0

  name        = "${var.env}-${var.identifier}-subnet-group"
  description = "Subnet group for ${var.identifier} RDS instance"
  subnet_ids  = var.subnet_ids

  tags = local.tags
}

# DB parameter group
resource "aws_db_parameter_group" "this" {
  count = var.create_parameter_group ? 1 : 0

  name        = "${var.env}-${var.identifier}-parameter-group"
  description = "Parameter group for ${var.identifier} RDS instance"
  family      = var.parameter_group_family

  dynamic "parameter" {
    for_each = var.db_parameters
    content {
      name  = parameter.key
      value = parameter.value
    }
  }

  tags = local.tags
}

# DB option group
resource "aws_db_option_group" "this" {
  count = var.create_option_group ? 1 : 0

  name                     = "${var.env}-${var.identifier}-option-group"
  option_group_description = "Option group for ${var.identifier} RDS instance"
  engine_name              = var.engine
  major_engine_version     = var.major_engine_version

  dynamic "option" {
    for_each = var.db_options
    content {
      option_name = option.value.option_name

      dynamic "option_settings" {
        for_each = option.value.option_settings
        content {
          name  = option_settings.key
          value = option_settings.value
        }
      }
    }
  }

  tags = local.tags
}

# Security group for RDS
resource "aws_security_group" "this" {
  count = var.create_security_group ? 1 : 0

  name        = "${var.env}-${var.identifier}-sg"
  description = "Security group for ${var.identifier} RDS instance"
  vpc_id      = var.vpc_id

  tags = local.tags
}

resource "aws_security_group_rule" "ingress" {
  count = var.create_security_group ? length(var.allowed_cidr_blocks) : 0

  type              = "ingress"
  from_port         = var.port
  to_port           = var.port
  protocol          = "tcp"
  cidr_blocks       = [var.allowed_cidr_blocks[count.index]]
  security_group_id = aws_security_group.this[0].id
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

  description             = "KMS key for ${var.identifier} RDS instance"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.tags
}

resource "aws_kms_alias" "this" {
  count = var.create_kms_key ? 1 : 0

  name          = "alias/${var.env}-${var.identifier}-rds"
  target_key_id = aws_kms_key.this[0].key_id
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "this" {
  for_each = toset(var.enabled_cloudwatch_logs_exports)

  name              = "/aws/rds/instance/${var.env}-${var.identifier}/${each.value}"
  retention_in_days = var.cloudwatch_log_retention_days
  kms_key_id        = var.create_kms_key ? aws_kms_key.this[0].arn : var.kms_key_arn

  tags = local.tags
}

# RDS instance
resource "aws_db_instance" "this" {
  identifier = "${var.env}-${var.identifier}"

  # Engine options
  engine                  = var.engine
  engine_version          = var.engine_version
  license_model           = var.license_model
  parameter_group_name    = local.parameter_group_name
  option_group_name       = local.option_group_name
  auto_minor_version_upgrade = var.auto_minor_version_upgrade

  # Instance specifications
  instance_class          = var.instance_class
  storage_type            = var.storage_type
  allocated_storage       = var.allocated_storage
  max_allocated_storage   = var.max_allocated_storage
  storage_encrypted       = true
  kms_key_id              = var.create_kms_key ? aws_kms_key.this[0].arn : var.kms_key_arn
  db_name                 = var.database_name
  port                    = var.port

  # Authentication
  username               = var.username
  password               = var.create_random_password ? random_password.master_password[0].result : var.password
  iam_database_authentication_enabled = var.iam_database_authentication_enabled
  domain                 = var.domain
  domain_iam_role_name   = var.domain_iam_role_name

  # Network
  multi_az               = var.multi_az
  db_subnet_group_name   = local.subnet_group_name
  publicly_accessible    = var.publicly_accessible
  vpc_security_group_ids = var.create_security_group ? [aws_security_group.this[0].id] : var.vpc_security_group_ids

  # Backup and maintenance
  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window
  copy_tags_to_snapshot   = true
  skip_final_snapshot     = var.skip_final_snapshot
  final_snapshot_identifier = "${var.env}-${var.identifier}-final-${formatdate("YYYYMMDD-hhmmss", timestamp())}"
  deletion_protection     = var.deletion_protection

  # Monitoring
  monitoring_interval     = var.monitoring_interval
  monitoring_role_arn     = var.monitoring_role_arn
  enabled_cloudwatch_logs_exports = var.enabled_cloudwatch_logs_exports
  performance_insights_enabled    = var.performance_insights_enabled
  performance_insights_kms_key_id = var.performance_insights_enabled ? (var.create_kms_key ? aws_kms_key.this[0].arn : var.kms_key_arn) : null
  performance_insights_retention_period = var.performance_insights_retention_period

  # Lifecycle management
  lifecycle {
    ignore_changes = [
      final_snapshot_identifier,
    ]
  }

  tags = local.tags
}

# Enhanced monitoring IAM role
resource "aws_iam_role" "enhanced_monitoring" {
  count = var.create_monitoring_role && var.monitoring_interval > 0 ? 1 : 0

  name = "${var.env}-${var.identifier}-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      },
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  ]

  tags = local.tags
}

# CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = var.create_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.env}-${var.identifier}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Monitors high CPU utilization for ${var.identifier} RDS instance"
  alarm_actions       = var.cloudwatch_alarm_actions
  ok_actions          = var.cloudwatch_ok_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "memory_freeable" {
  count = var.create_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.env}-${var.identifier}-low-memory-freeable"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 524288000 # 500MB in bytes
  alarm_description   = "Monitors low freeable memory for ${var.identifier} RDS instance"
  alarm_actions       = var.cloudwatch_alarm_actions
  ok_actions          = var.cloudwatch_ok_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "disk_free" {
  count = var.create_cloudwatch_alarms ? 1 : 0

  alarm_name          = "${var.env}-${var.identifier}-low-disk-free"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.allocated_storage * 1024 * 1024 * 1024 * 0.2 # 20% of allocated storage in bytes
  alarm_description   = "Monitors low free storage space for ${var.identifier} RDS instance"
  alarm_actions       = var.cloudwatch_alarm_actions
  ok_actions          = var.cloudwatch_ok_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }

  tags = local.tags
} 