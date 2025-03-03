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
}

# ECS Cluster
resource "aws_ecs_cluster" "this" {
  name = "${var.env}-${var.name}"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.ecs_exec.name
      }
    }
  }

  tags = local.tags
}

# CloudWatch Log Group for ECS Exec
resource "aws_cloudwatch_log_group" "ecs_exec" {
  name              = "/aws/ecs/${var.env}-${var.name}-exec"
  retention_in_days = var.log_retention_in_days
  kms_key_id        = var.kms_key_arn

  tags = local.tags
}

# CloudWatch Log Group for ECS Services
resource "aws_cloudwatch_log_group" "ecs_services" {
  name              = "/aws/ecs/${var.env}-${var.name}"
  retention_in_days = var.log_retention_in_days
  kms_key_id        = var.kms_key_arn

  tags = local.tags
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.env}-${var.name}-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  ]

  dynamic "inline_policy" {
    for_each = var.task_execution_role_additional_policies
    content {
      name   = inline_policy.key
      policy = inline_policy.value
    }
  }

  tags = local.tags
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.env}-${var.name}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  dynamic "inline_policy" {
    for_each = var.task_role_additional_policies
    content {
      name   = inline_policy.key
      policy = inline_policy.value
    }
  }

  tags = local.tags
}

# ECS Task Definitions
resource "aws_ecs_task_definition" "this" {
  for_each = var.task_definitions

  family                   = "${var.env}-${var.name}-${each.key}"
  network_mode             = each.value.network_mode
  requires_compatibilities = each.value.requires_compatibilities
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  container_definitions    = each.value.container_definitions
  runtime_platform {
    operating_system_family = each.value.operating_system_family
    cpu_architecture        = each.value.cpu_architecture
  }

  dynamic "volume" {
    for_each = each.value.volumes != null ? each.value.volumes : {}
    content {
      name = volume.key
      
      dynamic "efs_volume_configuration" {
        for_each = volume.value.efs_volume_configuration != null ? [volume.value.efs_volume_configuration] : []
        content {
          file_system_id     = efs_volume_configuration.value.file_system_id
          root_directory     = lookup(efs_volume_configuration.value, "root_directory", "/")
          transit_encryption = lookup(efs_volume_configuration.value, "transit_encryption", "ENABLED")
          
          dynamic "authorization_config" {
            for_each = efs_volume_configuration.value.authorization_config != null ? [efs_volume_configuration.value.authorization_config] : []
            content {
              access_point_id = authorization_config.value.access_point_id
              iam             = lookup(authorization_config.value, "iam", "ENABLED")
            }
          }
        }
      }
    }
  }

  tags = local.tags
}

# ECS Services
resource "aws_ecs_service" "this" {
  for_each = var.services

  name                               = "${var.env}-${var.name}-${each.key}"
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.this[each.value.task_definition].arn
  desired_count                      = each.value.desired_count
  deployment_minimum_healthy_percent = each.value.deployment_minimum_healthy_percent
  deployment_maximum_percent         = each.value.deployment_maximum_percent
  health_check_grace_period_seconds  = each.value.health_check_grace_period_seconds
  launch_type                        = each.value.launch_type
  platform_version                   = each.value.platform_version
  scheduling_strategy                = each.value.scheduling_strategy
  enable_execute_command             = each.value.enable_execute_command
  force_new_deployment               = each.value.force_new_deployment

  dynamic "network_configuration" {
    for_each = each.value.network_configuration != null ? [each.value.network_configuration] : []
    content {
      subnets          = network_configuration.value.subnets
      security_groups  = network_configuration.value.security_groups
      assign_public_ip = network_configuration.value.assign_public_ip
    }
  }

  dynamic "load_balancer" {
    for_each = each.value.load_balancers != null ? each.value.load_balancers : []
    content {
      target_group_arn = load_balancer.value.target_group_arn
      container_name   = load_balancer.value.container_name
      container_port   = load_balancer.value.container_port
    }
  }

  dynamic "service_registries" {
    for_each = each.value.service_registries != null ? [each.value.service_registries] : []
    content {
      registry_arn   = service_registries.value.registry_arn
      port           = lookup(service_registries.value, "port", null)
      container_name = lookup(service_registries.value, "container_name", null)
      container_port = lookup(service_registries.value, "container_port", null)
    }
  }

  deployment_controller {
    type = each.value.deployment_controller_type
  }

  lifecycle {
    ignore_changes = [
      desired_count
    ]
  }

  tags = local.tags
}

# Auto Scaling
resource "aws_appautoscaling_target" "this" {
  for_each = {
    for k, v in var.services : k => v if v.enable_autoscaling
  }

  max_capacity       = each.value.autoscaling_max_capacity
  min_capacity       = each.value.autoscaling_min_capacity
  resource_id        = "service/${aws_ecs_cluster.this.name}/${aws_ecs_service.this[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  for_each = {
    for k, v in var.services : k => v if v.enable_autoscaling && v.autoscaling_cpu_target > 0
  }

  name               = "${var.env}-${var.name}-${each.key}-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.this[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.this[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = each.value.autoscaling_cpu_target
    scale_in_cooldown  = each.value.autoscaling_scale_in_cooldown
    scale_out_cooldown = each.value.autoscaling_scale_out_cooldown
  }
}

resource "aws_appautoscaling_policy" "memory" {
  for_each = {
    for k, v in var.services : k => v if v.enable_autoscaling && v.autoscaling_memory_target > 0
  }

  name               = "${var.env}-${var.name}-${each.key}-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.this[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.this[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = each.value.autoscaling_memory_target
    scale_in_cooldown  = each.value.autoscaling_scale_in_cooldown
    scale_out_cooldown = each.value.autoscaling_scale_out_cooldown
  }
} 