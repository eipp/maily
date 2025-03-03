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

# Application Load Balancer Security Group
resource "aws_security_group" "alb" {
  count = var.create_alb_sg ? 1 : 0

  name        = "${var.name}-alb-sg"
  description = "Security group for application load balancer"
  vpc_id      = var.vpc_id

  tags = merge(
    local.tags,
    {
      Name = "${var.name}-alb-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "alb_ingress_http" {
  count = var.create_alb_sg && var.alb_ingress_http_enabled ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = var.alb_ingress_cidr_blocks
  description       = "Allow HTTP inbound traffic"
}

resource "aws_security_group_rule" "alb_ingress_https" {
  count = var.create_alb_sg && var.alb_ingress_https_enabled ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = var.alb_ingress_cidr_blocks
  description       = "Allow HTTPS inbound traffic"
}

resource "aws_security_group_rule" "alb_egress" {
  count = var.create_alb_sg ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# ECS Tasks Security Group
resource "aws_security_group" "ecs_tasks" {
  count = var.create_ecs_tasks_sg ? 1 : 0

  name        = "${var.name}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  tags = merge(
    local.tags,
    {
      Name = "${var.name}-ecs-tasks-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "ecs_ingress_from_alb" {
  count = var.create_ecs_tasks_sg && var.create_alb_sg ? 1 : 0

  security_group_id        = aws_security_group.ecs_tasks[0].id
  type                     = "ingress"
  from_port                = var.container_port
  to_port                  = var.container_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb[0].id
  description              = "Allow inbound traffic from ALB"
}

resource "aws_security_group_rule" "ecs_ingress_self" {
  count = var.create_ecs_tasks_sg && var.ecs_ingress_self_enabled ? 1 : 0

  security_group_id = aws_security_group.ecs_tasks[0].id
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  self              = true
  description       = "Allow all inbound traffic from self"
}

resource "aws_security_group_rule" "ecs_egress" {
  count = var.create_ecs_tasks_sg ? 1 : 0

  security_group_id = aws_security_group.ecs_tasks[0].id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# Database Security Group
resource "aws_security_group" "database" {
  count = var.create_database_sg ? 1 : 0

  name        = "${var.name}-database-sg"
  description = "Security group for database"
  vpc_id      = var.vpc_id

  tags = merge(
    local.tags,
    {
      Name = "${var.name}-database-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "database_ingress_from_ecs" {
  count = var.create_database_sg && var.create_ecs_tasks_sg ? 1 : 0

  security_group_id        = aws_security_group.database[0].id
  type                     = "ingress"
  from_port                = var.database_port
  to_port                  = var.database_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ecs_tasks[0].id
  description              = "Allow inbound traffic from ECS tasks"
}

resource "aws_security_group_rule" "database_egress" {
  count = var.create_database_sg ? 1 : 0

  security_group_id = aws_security_group.database[0].id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# Redis/ElastiCache Security Group
resource "aws_security_group" "redis" {
  count = var.create_redis_sg ? 1 : 0

  name        = "${var.name}-redis-sg"
  description = "Security group for Redis/ElastiCache"
  vpc_id      = var.vpc_id

  tags = merge(
    local.tags,
    {
      Name = "${var.name}-redis-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "redis_ingress_from_ecs" {
  count = var.create_redis_sg && var.create_ecs_tasks_sg ? 1 : 0

  security_group_id        = aws_security_group.redis[0].id
  type                     = "ingress"
  from_port                = var.redis_port
  to_port                  = var.redis_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ecs_tasks[0].id
  description              = "Allow inbound traffic from ECS tasks"
}

resource "aws_security_group_rule" "redis_egress" {
  count = var.create_redis_sg ? 1 : 0

  security_group_id = aws_security_group.redis[0].id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# VPN/Bastion Security Group
resource "aws_security_group" "bastion" {
  count = var.create_bastion_sg ? 1 : 0

  name        = "${var.name}-bastion-sg"
  description = "Security group for VPN/Bastion"
  vpc_id      = var.vpc_id

  tags = merge(
    local.tags,
    {
      Name = "${var.name}-bastion-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "bastion_ingress_ssh" {
  count = var.create_bastion_sg ? 1 : 0

  security_group_id = aws_security_group.bastion[0].id
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = var.bastion_ingress_cidr_blocks
  description       = "Allow SSH inbound traffic"
}

resource "aws_security_group_rule" "bastion_egress" {
  count = var.create_bastion_sg ? 1 : 0

  security_group_id = aws_security_group.bastion[0].id
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
}

# Optional DB access from Bastion
resource "aws_security_group_rule" "database_ingress_from_bastion" {
  count = var.create_database_sg && var.create_bastion_sg && var.allow_db_access_from_bastion ? 1 : 0

  security_group_id        = aws_security_group.database[0].id
  type                     = "ingress"
  from_port                = var.database_port
  to_port                  = var.database_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion[0].id
  description              = "Allow inbound traffic from Bastion"
}

# Optional Redis access from Bastion
resource "aws_security_group_rule" "redis_ingress_from_bastion" {
  count = var.create_redis_sg && var.create_bastion_sg && var.allow_redis_access_from_bastion ? 1 : 0

  security_group_id        = aws_security_group.redis[0].id
  type                     = "ingress"
  from_port                = var.redis_port
  to_port                  = var.redis_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion[0].id
  description              = "Allow inbound traffic from Bastion"
} 