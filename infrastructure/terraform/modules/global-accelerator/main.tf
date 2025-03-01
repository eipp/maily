provider "aws" {
  region = var.primary_region
}

# Create Global Accelerator
resource "aws_globalaccelerator_accelerator" "maily_accelerator" {
  name            = var.accelerator_name
  ip_address_type = "IPV4"
  enabled         = true

  attributes {
    flow_logs_enabled   = true
    flow_logs_s3_bucket = var.flow_logs_s3_bucket
    flow_logs_s3_prefix = var.flow_logs_s3_prefix
  }

  tags = {
    Name        = var.accelerator_name
    Environment = var.environment
  }
}

# Create listener for HTTP/HTTPS traffic
resource "aws_globalaccelerator_listener" "http_listener" {
  accelerator_arn = aws_globalaccelerator_accelerator.maily_accelerator.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"

  port_range {
    from_port = 80
    to_port   = 80
  }

  port_range {
    from_port = 443
    to_port   = 443
  }
}

# Create endpoint group for primary region
resource "aws_globalaccelerator_endpoint_group" "primary_endpoint_group" {
  listener_arn = aws_globalaccelerator_listener.http_listener.id

  endpoint_group_region = var.primary_region

  health_check_port             = 80
  health_check_protocol         = "HTTP"
  health_check_path             = "/health"
  health_check_interval_seconds = 30
  threshold_count               = 3

  traffic_dial_percentage = var.primary_traffic_dial

  dynamic "endpoint_configuration" {
    for_each = var.primary_alb_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }

  dynamic "endpoint_configuration" {
    for_each = var.primary_nlb_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }

  dynamic "endpoint_configuration" {
    for_each = var.primary_eip_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }

  dynamic "endpoint_configuration" {
    for_each = var.primary_ec2_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }
}

# Create endpoint group for secondary region
resource "aws_globalaccelerator_endpoint_group" "secondary_endpoint_group" {
  listener_arn = aws_globalaccelerator_listener.http_listener.id

  endpoint_group_region = var.secondary_region

  health_check_port             = 80
  health_check_protocol         = "HTTP"
  health_check_path             = "/health"
  health_check_interval_seconds = 30
  threshold_count               = 3

  traffic_dial_percentage = var.secondary_traffic_dial

  dynamic "endpoint_configuration" {
    for_each = var.secondary_alb_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }

  dynamic "endpoint_configuration" {
    for_each = var.secondary_nlb_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }

  dynamic "endpoint_configuration" {
    for_each = var.secondary_eip_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }

  dynamic "endpoint_configuration" {
    for_each = var.secondary_ec2_arns
    content {
      endpoint_id = endpoint_configuration.value
      weight      = 100
      client_ip_preservation_enabled = true
    }
  }
}

# Create Route53 record for the Global Accelerator
resource "aws_route53_record" "global_accelerator" {
  count   = var.create_dns_record ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.dns_name
  type    = "A"

  alias {
    name                   = aws_globalaccelerator_accelerator.maily_accelerator.dns_name
    zone_id                = "Z2BJ6XQ5FK7U4H"  # This is a fixed value for Global Accelerator
    evaluate_target_health = true
  }
}

# Create CloudWatch alarms for Global Accelerator
resource "aws_cloudwatch_metric_alarm" "accelerator_availability" {
  alarm_name          = "${var.accelerator_name}-availability"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "HealthyEndpointCount"
  namespace           = "AWS/GlobalAccelerator"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "This alarm monitors the availability of Global Accelerator endpoints"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions

  dimensions = {
    AcceleratorId = aws_globalaccelerator_accelerator.maily_accelerator.id
    ListenerArn   = aws_globalaccelerator_listener.http_listener.id
  }
}

resource "aws_cloudwatch_metric_alarm" "accelerator_processed_bytes" {
  alarm_name          = "${var.accelerator_name}-processed-bytes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ProcessedBytesIn"
  namespace           = "AWS/GlobalAccelerator"
  period              = 300
  statistic           = "Sum"
  threshold           = var.bytes_threshold
  alarm_description   = "This alarm monitors the incoming traffic processed by Global Accelerator"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions

  dimensions = {
    AcceleratorId = aws_globalaccelerator_accelerator.maily_accelerator.id
  }
}
