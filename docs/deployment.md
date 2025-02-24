# Deployment Guide

## Overview

This guide covers the deployment process for Maily, including infrastructure setup, deployment procedures, and performance tuning guidelines.

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0.0
- Docker
- Node.js >= 18
- Python >= 3.9

## Infrastructure Setup

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Configure Variables

Create `terraform.tfvars`:
```hcl
environment         = "production"
aws_region         = "us-east-1"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

frontend_cpu    = 1024
frontend_memory = 2048
backend_cpu     = 2048
backend_memory  = 4096

db_name     = "maily"
db_username = "maily_admin"
db_password = "your-secure-password"

redis_node_type = "cache.t3.medium"
```

### 3. Deploy Infrastructure

```bash
terraform plan -out=tfplan
terraform apply tfplan
```

## Application Deployment

### Frontend Deployment

1. Build the application:
   ```bash
   cd maily-frontend
   npm install
   npm run build
   ```

2. Push to ECR:
   ```bash
   docker build -t maily/frontend .
   docker tag maily/frontend:latest $ECR_REPO/maily/frontend:latest
   docker push $ECR_REPO/maily/frontend:latest
   ```

### Backend Deployment

1. Build the application:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Push to ECR:
   ```bash
   docker build -t maily/backend .
   docker tag maily/backend:latest $ECR_REPO/maily/backend:latest
   docker push $ECR_REPO/maily/backend:latest
   ```

### Database Migrations

1. Run migrations:
   ```bash
   aws ecs run-task \
     --cluster maily-cluster \
     --task-definition maily-migrations \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
     --launch-type FARGATE
   ```

## Performance Tuning

### Frontend Performance

1. **Next.js Optimization**
   ```bash
   # Enable production optimizations
   NEXT_OPTIMIZE_FONTS=true
   NEXT_OPTIMIZE_IMAGES=true
   NEXT_OPTIMIZE_CSS=true
   ```

2. **Caching Strategy**
   - Configure CDN caching
   - Implement service worker
   - Use static generation where possible

3. **Bundle Optimization**
   ```bash
   # Analyze bundle size
   npm run analyze
   
   # Enable compression
   COMPRESS=true
   GZIP_COMPRESSION=true
   ```

### Backend Performance

1. **FastAPI Configuration**
   ```python
   # uvicorn configuration
   workers = multiprocessing.cpu_count() * 2 + 1
   worker_class = "uvicorn.workers.UvicornWorker"
   ```

2. **Database Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_campaign_user ON campaigns(user_id);
   CREATE INDEX idx_campaign_status ON campaigns(status);
   ```

3. **Redis Caching**
   ```python
   # Configure Redis
   REDIS_MAX_CONNECTIONS = 10
   REDIS_SOCKET_TIMEOUT = 2
   REDIS_RETRY_ON_TIMEOUT = True
   ```

### Infrastructure Scaling

1. **ECS Auto Scaling**
   ```hcl
   resource "aws_appautoscaling_target" "ecs_target" {
     max_capacity       = 10
     min_capacity       = 2
     resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
     scalable_dimension = "ecs:service:DesiredCount"
     service_namespace  = "ecs"
   }
   ```

2. **RDS Optimization**
   ```sql
   -- Configure RDS parameters
   SET max_connections = 200;
   SET shared_buffers = '1GB';
   SET effective_cache_size = '3GB';
   ```

3. **ElastiCache Scaling**
   ```hcl
   resource "aws_elasticache_cluster" "redis" {
     cluster_id           = "maily-redis"
     engine              = "redis"
     node_type           = "cache.t3.medium"
     num_cache_nodes     = 2
     parameter_group_name = "default.redis6.x"
   }
   ```

## Monitoring and Alerts

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'maily-backend'
    static_configs:
      - targets: ['backend:8000']
  
  - job_name: 'maily-frontend'
    static_configs:
      - targets: ['frontend:3000']
```

### CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "cpu-utilization-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "CPUUtilization"
  namespace          = "AWS/ECS"
  period             = "300"
  statistic          = "Average"
  threshold          = "85"
}
```

## Security Considerations

### SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name maily.app;

    ssl_certificate /etc/nginx/ssl/maily.crt;
    ssl_certificate_key /etc/nginx/ssl/maily.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### WAF Rules

```hcl
resource "aws_wafv2_web_acl" "main" {
  name        = "maily-waf"
  description = "WAF rules for Maily"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   ```bash
   # Check ECS service events
   aws ecs describe-services \
     --cluster maily-cluster \
     --services maily-frontend maily-backend
   ```

2. **Database Connectivity**
   ```bash
   # Test database connection
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME
   ```

3. **Cache Issues**
   ```bash
   # Monitor Redis metrics
   redis-cli info stats
   ```

### Rollback Procedures

1. **Application Rollback**
   ```bash
   # Revert to previous version
   aws ecs update-service \
     --cluster maily-cluster \
     --service maily-frontend \
     --task-definition maily-frontend:previous
   ```

2. **Database Rollback**
   ```bash
   # Restore from snapshot
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier maily-db \
     --db-snapshot-identifier maily-snapshot
   ```

## Maintenance

### Backup Procedures

1. **Database Backups**
   ```bash
   # Manual snapshot
   aws rds create-db-snapshot \
     --db-instance-identifier maily-db \
     --db-snapshot-identifier maily-manual-backup
   ```

2. **Application State**
   ```bash
   # Export configurations
   aws s3 cp s3://maily-configs/prod/ ./backup/configs/ --recursive
   ```

### Updates and Patches

1. **OS Updates**
   ```bash
   # Update ECS container instances
   aws ecs update-container-instances-state \
     --cluster maily-cluster \
     --container-instances $INSTANCE_ID \
     --status DRAINING
   ```

2. **Dependencies**
   ```bash
   # Update npm packages
   npm audit fix
   
   # Update Python packages
   pip-compile requirements.in
   ``` 