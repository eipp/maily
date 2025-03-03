output "bucket_id" {
  description = "The name of the bucket"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "The ARN of the bucket"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "The bucket domain name"
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "The bucket region-specific domain name"
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "bucket_region" {
  description = "The AWS region the bucket resides in"
  value       = aws_s3_bucket.this.region
}

output "hosted_zone_id" {
  description = "The Route 53 Hosted Zone ID for this bucket's region"
  value       = aws_s3_bucket.this.hosted_zone_id
}

output "bucket_policy_id" {
  description = "The ID of the bucket policy"
  value       = var.attach_policy || var.policy != null ? aws_s3_bucket_policy.this[0].id : null
}

output "kms_key_id" {
  description = "The ID of the KMS key used for bucket encryption"
  value       = var.create_kms_key ? aws_kms_key.this[0].id : var.kms_key_id
}

output "kms_key_arn" {
  description = "The ARN of the KMS key used for bucket encryption"
  value       = var.create_kms_key ? aws_kms_key.this[0].arn : null
}

output "kms_key_alias_arn" {
  description = "The ARN of the KMS key alias"
  value       = var.create_kms_key ? aws_kms_alias.this[0].arn : null
}

output "public_access_block_id" {
  description = "The ID of the public access block configuration"
  value       = aws_s3_bucket_public_access_block.this.id
} 