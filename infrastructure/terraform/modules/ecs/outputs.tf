output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = var.create_cluster ? aws_ecs_cluster.this[0].id : var.cluster_id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = var.create_cluster ? aws_ecs_cluster.this[0].arn : null
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = var.create_cluster ? aws_ecs_cluster.this[0].name : null
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.this.arn
}

output "task_definition_family" {
  description = "Family of the task definition"
  value       = aws_ecs_task_definition.this.family
}

output "task_definition_revision" {
  description = "Revision of the task definition"
  value       = aws_ecs_task_definition.this.revision
}

output "service_id" {
  description = "ID of the service"
  value       = aws_ecs_service.this.id
}

output "service_name" {
  description = "Name of the service"
  value       = aws_ecs_service.this.name
}

output "service_arn" {
  description = "ARN of the service"
  value       = aws_ecs_service.this.arn
}

output "execution_role_arn" {
  description = "ARN of the execution role"
  value       = var.create_iam_roles ? aws_iam_role.execution[0].arn : var.execution_role_arn
}

output "execution_role_name" {
  description = "Name of the execution role"
  value       = var.create_iam_roles ? aws_iam_role.execution[0].name : null
}

output "task_role_arn" {
  description = "ARN of the task role"
  value       = var.create_iam_roles ? aws_iam_role.task[0].arn : var.task_role_arn
}

output "task_role_name" {
  description = "Name of the task role"
  value       = var.create_iam_roles ? aws_iam_role.task[0].name : null
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.this.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.this.arn
}

output "autoscaling_target_id" {
  description = "ID of the App Autoscaling Target"
  value       = var.enable_autoscaling ? aws_appautoscaling_target.this[0].id : null
}

output "autoscaling_policy_cpu_arn" {
  description = "ARN of the App Autoscaling Policy for CPU"
  value       = var.enable_autoscaling && var.autoscaling_cpu_enabled ? aws_appautoscaling_policy.cpu[0].arn : null
}

output "autoscaling_policy_memory_arn" {
  description = "ARN of the App Autoscaling Policy for memory"
  value       = var.enable_autoscaling && var.autoscaling_memory_enabled ? aws_appautoscaling_policy.memory[0].arn : null
}

output "autoscaling_policy_requests_arn" {
  description = "ARN of the App Autoscaling Policy for requests"
  value       = var.enable_autoscaling && var.autoscaling_requests_enabled && var.lb_target_group_arn != null ? aws_appautoscaling_policy.requests[0].arn : null
}

output "cloudwatch_alarm_cpu_arn" {
  description = "ARN of the CloudWatch Alarm for CPU high utilization"
  value       = var.create_alarms ? aws_cloudwatch_metric_alarm.service_high_cpu[0].arn : null
}

output "cloudwatch_alarm_memory_arn" {
  description = "ARN of the CloudWatch Alarm for memory high utilization"
  value       = var.create_alarms ? aws_cloudwatch_metric_alarm.service_high_memory[0].arn : null
} 