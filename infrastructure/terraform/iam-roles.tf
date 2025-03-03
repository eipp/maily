/**
 * IAM Roles Configuration for Service Accounts
 *
 * This Terraform configuration sets up IAM roles for Kubernetes service accounts
 * using IRSA (IAM Roles for Service Accounts) to enable secure access to AWS resources.
 */

# OIDC Provider for the EKS cluster
data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}

data "tls_certificate" "eks" {
  url = data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}

# IAM Role for S3 Access (used by backup and restore operations)
resource "aws_iam_role" "s3_access" {
  name = "maily-s3-access-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub": "system:serviceaccount:maily:backup-service"
          }
        }
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name = "maily-s3-access-${var.environment}"
      Environment = var.environment
    }
  )
}

resource "aws_iam_policy" "s3_access" {
  name        = "maily-s3-access-policy-${var.environment}"
  description = "Policy for S3 access for backup and restore operations"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:s3:::${var.backup_bucket_name}",
          "arn:aws:s3:::${var.backup_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_access" {
  role       = aws_iam_role.s3_access.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# IAM Role for CloudWatch Metrics (used by monitoring)
resource "aws_iam_role" "cloudwatch_metrics" {
  name = "maily-cloudwatch-metrics-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub": "system:serviceaccount:maily:monitoring-service"
          }
        }
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name = "maily-cloudwatch-metrics-${var.environment}"
      Environment = var.environment
    }
  )
}

resource "aws_iam_policy" "cloudwatch_metrics" {
  name        = "maily-cloudwatch-metrics-policy-${var.environment}"
  description = "Policy for CloudWatch metrics access"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_metrics" {
  role       = aws_iam_role.cloudwatch_metrics.name
  policy_arn = aws_iam_policy.cloudwatch_metrics.arn
}

# IAM Role for SES (used by email service)
resource "aws_iam_role" "ses_access" {
  name = "maily-ses-access-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub": "system:serviceaccount:maily:email-service"
          }
        }
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name = "maily-ses-access-${var.environment}"
      Environment = var.environment
    }
  )
}

resource "aws_iam_policy" "ses_access" {
  name        = "maily-ses-access-policy-${var.environment}"
  description = "Policy for SES access for sending emails"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail",
          "ses:GetSendQuota",
          "ses:GetSendStatistics"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ses_access" {
  role       = aws_iam_role.ses_access.name
  policy_arn = aws_iam_policy.ses_access.arn
}

# IAM Role for DynamoDB (used by analytics service)
resource "aws_iam_role" "dynamodb_access" {
  name = "maily-dynamodb-access-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub": "system:serviceaccount:maily:analytics-service"
          }
        }
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name = "maily-dynamodb-access-${var.environment}"
      Environment = var.environment
    }
  )
}

resource "aws_iam_policy" "dynamodb_access" {
  name        = "maily-dynamodb-access-policy-${var.environment}"
  description = "Policy for DynamoDB access for analytics service"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/maily-analytics-*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "dynamodb_access" {
  role       = aws_iam_role.dynamodb_access.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

# IAM Role for Secrets Manager (used by all services)
resource "aws_iam_role" "secrets_manager_access" {
  name = "maily-secrets-manager-access-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud": "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = merge(
    var.common_tags,
    {
      Name = "maily-secrets-manager-access-${var.environment}"
      Environment = var.environment
    }
  )
}

resource "aws_iam_policy" "secrets_manager_access" {
  name        = "maily-secrets-manager-access-policy-${var.environment}"
  description = "Policy for Secrets Manager access"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:maily-*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_manager_access" {
  role       = aws_iam_role.secrets_manager_access.name
  policy_arn = aws_iam_policy.secrets_manager_access.arn
}

# Output the IAM role ARNs
output "s3_access_role_arn" {
  description = "The ARN of the S3 access IAM role"
  value       = aws_iam_role.s3_access.arn
}

output "cloudwatch_metrics_role_arn" {
  description = "The ARN of the CloudWatch metrics IAM role"
  value       = aws_iam_role.cloudwatch_metrics.arn
}

output "ses_access_role_arn" {
  description = "The ARN of the SES access IAM role"
  value       = aws_iam_role.ses_access.arn
}

output "dynamodb_access_role_arn" {
  description = "The ARN of the DynamoDB access IAM role"
  value       = aws_iam_role.dynamodb_access.arn
}

output "secrets_manager_access_role_arn" {
  description = "The ARN of the Secrets Manager access IAM role"
  value       = aws_iam_role.secrets_manager_access.arn
}
