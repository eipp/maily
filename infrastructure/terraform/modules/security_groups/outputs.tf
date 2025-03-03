output "alb_security_group_id" {
  description = "ID of the security group for the Application Load Balancer"
  value       = var.create_alb_sg ? aws_security_group.alb[0].id : null
}

output "alb_security_group_arn" {
  description = "ARN of the security group for the Application Load Balancer"
  value       = var.create_alb_sg ? aws_security_group.alb[0].arn : null
}

output "ecs_tasks_security_group_id" {
  description = "ID of the security group for ECS tasks"
  value       = var.create_ecs_tasks_sg ? aws_security_group.ecs_tasks[0].id : null
}

output "ecs_tasks_security_group_arn" {
  description = "ARN of the security group for ECS tasks"
  value       = var.create_ecs_tasks_sg ? aws_security_group.ecs_tasks[0].arn : null
}

output "database_security_group_id" {
  description = "ID of the security group for the database"
  value       = var.create_database_sg ? aws_security_group.database[0].id : null
}

output "database_security_group_arn" {
  description = "ARN of the security group for the database"
  value       = var.create_database_sg ? aws_security_group.database[0].arn : null
}

output "redis_security_group_id" {
  description = "ID of the security group for Redis/ElastiCache"
  value       = var.create_redis_sg ? aws_security_group.redis[0].id : null
}

output "redis_security_group_arn" {
  description = "ARN of the security group for Redis/ElastiCache"
  value       = var.create_redis_sg ? aws_security_group.redis[0].arn : null
}

output "bastion_security_group_id" {
  description = "ID of the security group for bastion/VPN hosts"
  value       = var.create_bastion_sg ? aws_security_group.bastion[0].id : null
}

output "bastion_security_group_arn" {
  description = "ARN of the security group for bastion/VPN hosts"
  value       = var.create_bastion_sg ? aws_security_group.bastion[0].arn : null
}

output "security_group_ids" {
  description = "Map of all security group IDs created by this module"
  value = {
    alb       = var.create_alb_sg ? aws_security_group.alb[0].id : null
    ecs_tasks = var.create_ecs_tasks_sg ? aws_security_group.ecs_tasks[0].id : null
    database  = var.create_database_sg ? aws_security_group.database[0].id : null
    redis     = var.create_redis_sg ? aws_security_group.redis[0].id : null
    bastion   = var.create_bastion_sg ? aws_security_group.bastion[0].id : null
  }
} 