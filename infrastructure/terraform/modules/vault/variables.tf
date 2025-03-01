variable "region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-west-2"
}

variable "vpc_id" {
  description = "The VPC ID to deploy Vault in"
  type        = string
}

variable "subnet_id" {
  description = "The subnet ID to deploy Vault in"
  type        = string
}

variable "ami_id" {
  description = "The AMI ID to use for the Vault server"
  type        = string
}

variable "instance_type" {
  description = "The instance type to use for the Vault server"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "The key pair name to use for the Vault server"
  type        = string
}

variable "route53_zone_id" {
  description = "The Route53 zone ID to create the Vault DNS record in"
  type        = string
}

variable "domain_name" {
  description = "The domain name to use for the Vault server"
  type        = string
}
