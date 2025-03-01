output "vault_url" {
  description = "The URL of the Vault server"
  value       = "https://vault.${var.domain_name}:8200"
}

output "vault_public_ip" {
  description = "The public IP of the Vault server"
  value       = aws_eip.vault.public_ip
}

output "vault_kms_key_id" {
  description = "The ID of the KMS key used for Vault auto-unseal"
  value       = aws_kms_key.vault_kms.id
}
