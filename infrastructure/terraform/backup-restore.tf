/**
 * Backup and Restore Infrastructure
 *
 * This Terraform configuration sets up the infrastructure for backup and restore operations,
 * including S3 buckets, lifecycle policies, and IAM roles.
 */

# S3 bucket for backups
resource "aws_s3_bucket" "backup" {
  bucket = var.backup_bucket_name
  
  tags = merge(
    var.common_tags,
    {
      Name = var.backup_bucket_name
      Environment = var.environment
    }
  )
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "backup_versioning" {
  bucket = aws_s3_bucket.backup.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "backup_encryption" {
  bucket = aws_s3_bucket.backup.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket lifecycle policy
resource "aws_s3_bucket_lifecycle_configuration" "backup_lifecycle" {
  bucket = aws_s3_bucket.backup.id
  
  rule {
    id = "daily-backups"
    status = "Enabled"
    
    filter {
      prefix = "daily/"
    }
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
  
  rule {
    id = "weekly-backups"
    status = "Enabled"
    
    filter {
      prefix = "weekly/"
    }
    
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 180
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 730
    }
  }
  
  rule {
    id = "monthly-backups"
    status = "Enabled"
    
    filter {
      prefix = "monthly/"
    }
    
    transition {
      days          = 180
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 2555  # ~7 years
    }
  }
}

# S3 bucket for database backups
resource "aws_s3_bucket" "db_backup" {
  bucket = "${var.backup_bucket_name}-db"
  
  tags = merge(
    var.common_tags,
    {
      Name = "${var.backup_bucket_name}-db"
      Environment = var.environment
    }
  )
}

# S3 bucket versioning for database backups
resource "aws_s3_bucket_versioning" "db_backup_versioning" {
  bucket = aws_s3_bucket.db_backup.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption for database backups
resource "aws_s3_bucket_server_side_encryption_configuration" "db_backup_encryption" {
  bucket = aws_s3_bucket.db_backup.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket lifecycle policy for database backups
resource "aws_s3_bucket_lifecycle_configuration" "db_backup_lifecycle" {
  bucket = aws_s3_bucket.db_backup.id
  
  rule {
    id = "db-backups"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }
    
    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }
    
    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# DynamoDB table for backup metadata
resource "aws_dynamodb_table" "backup_metadata" {
  name           = "maily-backup-metadata-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "BackupId"
  range_key      = "Timestamp"
  
  attribute {
    name = "BackupId"
    type = "S"
  }
  
  attribute {
    name = "Timestamp"
    type = "N"
  }
  
  attribute {
    name = "Type"
    type = "S"
  }
  
  global_secondary_index {
    name               = "TypeIndex"
    hash_key           = "Type"
    range_key          = "Timestamp"
    projection_type    = "ALL"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-backup-metadata-${var.environment}"
      Environment = var.environment
    }
  )
}

# CloudWatch Event Rule for scheduled backups
resource "aws_cloudwatch_event_rule" "scheduled_backup" {
  name                = "maily-scheduled-backup-${var.environment}"
  description         = "Trigger scheduled backups for Maily"
  schedule_expression = "cron(0 1 * * ? *)"  # Daily at 1:00 AM UTC
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-scheduled-backup-${var.environment}"
      Environment = var.environment
    }
  )
}

# CloudWatch Event Target for scheduled backups
resource "aws_cloudwatch_event_target" "backup_lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled_backup.name
  target_id = "TriggerBackupLambda"
  arn       = aws_lambda_function.backup_trigger.arn
}

# Lambda function to trigger backups
resource "aws_lambda_function" "backup_trigger" {
  function_name    = "maily-backup-trigger-${var.environment}"
  role             = aws_iam_role.backup_lambda_role.arn
  handler          = "index.handler"
  runtime          = "nodejs18.x"
  timeout          = 300
  memory_size      = 256
  
  filename         = "${path.module}/lambda/backup-trigger.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda/backup-trigger.zip")
  
  environment {
    variables = {
      BACKUP_BUCKET_NAME = aws_s3_bucket.backup.bucket
      DB_BACKUP_BUCKET_NAME = aws_s3_bucket.db_backup.bucket
      BACKUP_METADATA_TABLE = aws_dynamodb_table.backup_metadata.name
      ENVIRONMENT = var.environment
      CLUSTER_NAME = var.cluster_name
      NAMESPACE = "maily"
    }
  }
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-backup-trigger-${var.environment}"
      Environment = var.environment
    }
  )
}

# IAM role for backup Lambda function
resource "aws_iam_role" "backup_lambda_role" {
  name = "maily-backup-lambda-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(
    var.common_tags,
    {
      Name = "maily-backup-lambda-role-${var.environment}"
      Environment = var.environment
    }
  )
}

# IAM policy for backup Lambda function
resource "aws_iam_policy" "backup_lambda_policy" {
  name        = "maily-backup-lambda-policy-${var.environment}"
  description = "Policy for backup Lambda function"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.backup.arn,
          "${aws_s3_bucket.backup.arn}/*",
          aws_s3_bucket.db_backup.arn,
          "${aws_s3_bucket.db_backup.arn}/*"
        ]
      },
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.backup_metadata.arn
      },
      {
        Action = [
          "eks:DescribeCluster"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:eks:${var.aws_region}:${var.aws_account_id}:cluster/${var.cluster_name}"
      },
      {
        Action = [
          "eks:ListClusters"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Attach policy to IAM role
resource "aws_iam_role_policy_attachment" "backup_lambda_policy_attachment" {
  role       = aws_iam_role.backup_lambda_role.name
  policy_arn = aws_iam_policy.backup_lambda_policy.arn
}

# Lambda permission for CloudWatch Events
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backup_trigger.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_backup.arn
}

# Output the backup bucket name
output "backup_bucket_name" {
  description = "The name of the backup S3 bucket"
  value       = aws_s3_bucket.backup.bucket
}

# Output the database backup bucket name
output "db_backup_bucket_name" {
  description = "The name of the database backup S3 bucket"
  value       = aws_s3_bucket.db_backup.bucket
}

# Output the backup metadata table name
output "backup_metadata_table_name" {
  description = "The name of the backup metadata DynamoDB table"
  value       = aws_dynamodb_table.backup_metadata.name
}
