# Provider configuration will be passed from the root module

resource "aws_kms_key" "vault_kms" {
  description             = "KMS Key for Vault auto-unseal"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "vault-kms-key"
  }
}

resource "aws_kms_alias" "vault_kms_alias" {
  name          = "alias/vault-kms-key"
  target_key_id = aws_kms_key.vault_kms.key_id
}

resource "aws_security_group" "vault" {
  name        = "vault-sg"
  description = "Security group for Vault"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8200
    to_port     = 8200
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8201
    to_port     = 8201
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "vault-sg"
  }
}

resource "aws_iam_role" "vault" {
  name = "vault-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "vault_kms" {
  name = "vault-kms"
  role = aws_iam_role.vault.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Effect   = "Allow"
        Resource = aws_kms_key.vault_kms.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "vault" {
  name = "vault-instance-profile"
  role = aws_iam_role.vault.name
}

resource "aws_instance" "vault" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.vault.id]
  subnet_id              = var.subnet_id
  iam_instance_profile   = aws_iam_instance_profile.vault.name

  user_data = templatefile("${path.module}/templates/user_data.tpl", {
    region     = var.region
    kms_key_id = aws_kms_key.vault_kms.id
  })

  tags = {
    Name = "vault-server"
  }
}

resource "aws_eip" "vault" {
  instance = aws_instance.vault.id
  domain   = "vpc"

  tags = {
    Name = "vault-eip"
  }
}

resource "aws_route53_record" "vault" {
  zone_id = var.route53_zone_id
  name    = "vault.${var.domain_name}"
  type    = "A"
  ttl     = "300"
  records = [aws_eip.vault.public_ip]
}
