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

resource "aws_kms_key" "this" {
  count = var.create_kms_key ? 1 : 0

  description             = "KMS key for ${var.name} S3 bucket encryption"
  deletion_window_in_days = var.kms_key_deletion_window_in_days
  enable_key_rotation     = var.kms_key_enable_rotation
  policy                  = var.kms_key_policy

  tags = local.tags
}

resource "aws_kms_alias" "this" {
  count = var.create_kms_key ? 1 : 0

  name          = "alias/${var.name}-s3"
  target_key_id = aws_kms_key.this[0].key_id
}

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  
  tags = local.tags

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = var.block_public_acls
  block_public_policy     = var.block_public_policy
  ignore_public_acls      = var.ignore_public_acls
  restrict_public_buckets = var.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.create_kms_key || var.kms_key_id != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.create_kms_key ? aws_kms_key.this[0].arn : var.kms_key_id
    }
    bucket_key_enabled = var.bucket_key_enabled
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count = length(var.lifecycle_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = var.lifecycle_rules

    content {
      id      = rule.value.id
      status  = rule.value.enabled ? "Enabled" : "Disabled"
      
      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        
        content {
          days = expiration.value.days
        }
      }
      
      dynamic "transition" {
        for_each = rule.value.transitions != null ? rule.value.transitions : []
        
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }
      
      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration != null ? [rule.value.noncurrent_version_expiration] : []
        
        content {
          noncurrent_days = noncurrent_version_expiration.value.days
        }
      }
      
      dynamic "noncurrent_version_transition" {
        for_each = rule.value.noncurrent_version_transitions != null ? rule.value.noncurrent_version_transitions : []
        
        content {
          noncurrent_days = noncurrent_version_transition.value.days
          storage_class   = noncurrent_version_transition.value.storage_class
        }
      }
      
      dynamic "abort_incomplete_multipart_upload" {
        for_each = rule.value.abort_incomplete_multipart_upload_days != null ? [rule.value.abort_incomplete_multipart_upload_days] : []
        
        content {
          days_after_initiation = abort_incomplete_multipart_upload.value
        }
      }
    }
  }
}

resource "aws_s3_bucket_logging" "this" {
  count = var.access_log_bucket_name != null ? 1 : 0

  bucket = aws_s3_bucket.this.id

  target_bucket = var.access_log_bucket_name
  target_prefix = var.access_log_prefix
}

resource "aws_s3_bucket_policy" "this" {
  count = var.attach_policy || var.policy != null ? 1 : 0

  bucket = aws_s3_bucket.this.id
  policy = var.policy != null ? var.policy : data.aws_iam_policy_document.bucket_policy[0].json
}

data "aws_iam_policy_document" "bucket_policy" {
  count = var.attach_policy && var.policy == null ? 1 : 0

  # Enforce HTTPS
  dynamic "statement" {
    for_each = var.enforce_ssl ? [1] : []
    
    content {
      sid     = "EnforceHTTPS"
      effect  = "Deny"
      actions = ["s3:*"]
      
      resources = [
        aws_s3_bucket.this.arn,
        "${aws_s3_bucket.this.arn}/*"
      ]
      
      principals {
        type        = "*"
        identifiers = ["*"]
      }
      
      condition {
        test     = "Bool"
        variable = "aws:SecureTransport"
        values   = ["false"]
      }
    }
  }
}

# CloudWatch Metric Alarms
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  count = var.create_monitoring_alarms ? 1 : 0

  alarm_name          = "${var.name}-s3-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "4xxErrors"
  namespace           = "AWS/S3"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "This metric monitors S3 bucket 4xx errors"
  alarm_actions       = var.alarm_actions
  ok_actions          = var.ok_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    BucketName = aws_s3_bucket.this.id
  }

  tags = local.tags
} 