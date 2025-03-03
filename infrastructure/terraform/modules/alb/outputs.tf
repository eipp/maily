output "id" {
  description = "ID of the application load balancer"
  value       = aws_lb.this.id
}

output "arn" {
  description = "ARN of the application load balancer"
  value       = aws_lb.this.arn
}

output "arn_suffix" {
  description = "ARN suffix of the application load balancer for use with CloudWatch Metrics"
  value       = aws_lb.this.arn_suffix
}

output "dns_name" {
  description = "DNS name of the application load balancer"
  value       = aws_lb.this.dns_name
}

output "zone_id" {
  description = "Route53 zone ID of the application load balancer"
  value       = aws_lb.this.zone_id
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = var.create_http_listener ? aws_lb_listener.http[0].arn : null
}

output "https_listener_arn" {
  description = "ARN of the HTTPS listener"
  value       = var.create_https_listener ? aws_lb_listener.https[0].arn : null
}

output "default_target_group_arn" {
  description = "ARN of the default target group"
  value       = aws_lb_target_group.default[0].arn
}

output "default_target_group_id" {
  description = "ID of the default target group"
  value       = aws_lb_target_group.default[0].id
}

output "default_target_group_name" {
  description = "Name of the default target group"
  value       = aws_lb_target_group.default[0].name
}

output "default_target_group_arn_suffix" {
  description = "ARN suffix of the default target group for use with CloudWatch Metrics"
  value       = aws_lb_target_group.default[0].arn_suffix
}

output "additional_target_groups" {
  description = "Map of additional target groups created"
  value = {
    for idx, tg in aws_lb_target_group.additional :
    var.additional_target_groups[idx].name => {
      arn        = tg.arn
      arn_suffix = tg.arn_suffix
      id         = tg.id
      name       = tg.name
    }
  }
}

output "security_group_id" {
  description = "Security group ID associated with the ALB"
  value       = var.security_group_id
}

output "alb_5xx_alarm_id" {
  description = "ID of the CloudWatch alarm for 5XX errors on ALB"
  value       = var.create_alarms ? aws_cloudwatch_metric_alarm.alb_5xx_errors[0].id : null
}

output "alb_4xx_alarm_id" {
  description = "ID of the CloudWatch alarm for 4XX errors on ALB"
  value       = var.create_alarms ? aws_cloudwatch_metric_alarm.alb_4xx_errors[0].id : null
}

output "target_5xx_alarm_id" {
  description = "ID of the CloudWatch alarm for 5XX errors on targets"
  value       = var.create_alarms ? aws_cloudwatch_metric_alarm.target_5xx_errors[0].id : null
}

output "unhealthy_hosts_alarm_id" {
  description = "ID of the CloudWatch alarm for unhealthy hosts"
  value       = var.create_alarms ? aws_cloudwatch_metric_alarm.unhealthy_hosts[0].id : null
} 