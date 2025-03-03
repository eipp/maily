terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

locals {
  tags = merge(
    {
      Name        = var.name
      Environment = var.environment
      Terraform   = "true"
      Service     = "maily"
    },
    var.tags
  )
}

# Application Load Balancer
resource "aws_lb" "this" {
  name               = "${var.name}-alb"
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = [var.security_group_id]
  subnets            = var.subnet_ids

  enable_deletion_protection       = var.enable_deletion_protection
  enable_cross_zone_load_balancing = var.enable_cross_zone_load_balancing
  enable_http2                     = var.enable_http2
  idle_timeout                     = var.idle_timeout
  drop_invalid_header_fields       = var.drop_invalid_header_fields
  desync_mitigation_mode           = var.desync_mitigation_mode

  dynamic "access_logs" {
    for_each = var.access_logs_bucket != null ? [1] : []
    
    content {
      bucket  = var.access_logs_bucket
      prefix  = var.access_logs_prefix
      enabled = true
    }
  }

  tags = local.tags
}

# HTTP/HTTPS Listeners
resource "aws_lb_listener" "http" {
  count = var.create_http_listener ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = var.redirect_http_to_https ? [1] : []
    
    content {
      type = "redirect"

      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = var.redirect_http_to_https ? [] : [1]
    
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.default[0].arn
    }
  }

  tags = local.tags
}

resource "aws_lb_listener" "https" {
  count = var.create_https_listener ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.default[0].arn
  }

  tags = local.tags
}

# Default Target Group
resource "aws_lb_target_group" "default" {
  count = 1

  name                 = "${var.name}-default-tg"
  port                 = var.target_group_port
  protocol             = var.target_group_protocol
  vpc_id               = var.vpc_id
  target_type          = var.target_type
  deregistration_delay = var.deregistration_delay

  health_check {
    enabled             = true
    interval            = var.health_check_interval
    path                = var.health_check_path
    port                = var.health_check_port
    protocol            = var.health_check_protocol
    timeout             = var.health_check_timeout
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    matcher             = var.health_check_matcher
  }

  dynamic "stickiness" {
    for_each = var.stickiness_enabled ? [1] : []
    
    content {
      type            = var.stickiness_type
      cookie_duration = var.stickiness_cookie_duration
      enabled         = true
    }
  }

  tags = local.tags

  lifecycle {
    create_before_destroy = true
  }
}

# Additional Target Groups
resource "aws_lb_target_group" "additional" {
  count = length(var.additional_target_groups)

  name                 = "${var.name}-${var.additional_target_groups[count.index].name}-tg"
  port                 = lookup(var.additional_target_groups[count.index], "port", var.target_group_port)
  protocol             = lookup(var.additional_target_groups[count.index], "protocol", var.target_group_protocol)
  vpc_id               = var.vpc_id
  target_type          = lookup(var.additional_target_groups[count.index], "target_type", var.target_type)
  deregistration_delay = lookup(var.additional_target_groups[count.index], "deregistration_delay", var.deregistration_delay)

  health_check {
    enabled             = true
    interval            = lookup(var.additional_target_groups[count.index], "health_check_interval", var.health_check_interval)
    path                = lookup(var.additional_target_groups[count.index], "health_check_path", var.health_check_path)
    port                = lookup(var.additional_target_groups[count.index], "health_check_port", var.health_check_port)
    protocol            = lookup(var.additional_target_groups[count.index], "health_check_protocol", var.health_check_protocol)
    timeout             = lookup(var.additional_target_groups[count.index], "health_check_timeout", var.health_check_timeout)
    healthy_threshold   = lookup(var.additional_target_groups[count.index], "health_check_healthy_threshold", var.health_check_healthy_threshold)
    unhealthy_threshold = lookup(var.additional_target_groups[count.index], "health_check_unhealthy_threshold", var.health_check_unhealthy_threshold)
    matcher             = lookup(var.additional_target_groups[count.index], "health_check_matcher", var.health_check_matcher)
  }

  dynamic "stickiness" {
    for_each = lookup(var.additional_target_groups[count.index], "stickiness_enabled", var.stickiness_enabled) ? [1] : []
    
    content {
      type            = lookup(var.additional_target_groups[count.index], "stickiness_type", var.stickiness_type)
      cookie_duration = lookup(var.additional_target_groups[count.index], "stickiness_cookie_duration", var.stickiness_cookie_duration)
      enabled         = true
    }
  }

  tags = local.tags

  lifecycle {
    create_before_destroy = true
  }
}

# Additional Listener Rules
resource "aws_lb_listener_rule" "paths" {
  count = var.create_https_listener ? length(var.path_patterns) : 0

  listener_arn = aws_lb_listener.https[0].arn
  priority     = var.path_patterns[count.index].priority

  action {
    type             = "forward"
    target_group_arn = lookup(var.path_patterns[count.index], "target_group_index", null) != null ? aws_lb_target_group.additional[var.path_patterns[count.index].target_group_index].arn : aws_lb_target_group.default[0].arn
  }

  condition {
    path_pattern {
      values = var.path_patterns[count.index].path_patterns
    }
  }

  dynamic "condition" {
    for_each = lookup(var.path_patterns[count.index], "host_headers", null) != null ? [1] : []
    
    content {
      host_header {
        values = var.path_patterns[count.index].host_headers
      }
    }
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "${var.name}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = var.alarm_5xx_threshold
  alarm_description   = "This metric monitors the number of 5XX errors returned by the ALB"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.this.arn_suffix
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_4xx_errors" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "${var.name}-alb-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_ELB_4XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = var.alarm_4xx_threshold
  alarm_description   = "This metric monitors the number of 4XX errors returned by the ALB"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.this.arn_suffix
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "target_5xx_errors" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "${var.name}-target-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = var.alarm_target_5xx_threshold
  alarm_description   = "This metric monitors the number of 5XX errors returned by targets"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.this.arn_suffix
  }

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_hosts" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "${var.name}-unhealthy-hosts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Maximum"
  threshold           = var.alarm_unhealthy_hosts_threshold
  alarm_description   = "This metric monitors the number of unhealthy hosts"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.this.arn_suffix
    TargetGroup  = aws_lb_target_group.default[0].arn_suffix
  }

  tags = local.tags
}

# WAF Association (optional)
resource "aws_wafv2_web_acl_association" "alb" {
  count = var.waf_web_acl_arn != null ? 1 : 0

  resource_arn = aws_lb.this.arn
  web_acl_arn  = var.waf_web_acl_arn
} 