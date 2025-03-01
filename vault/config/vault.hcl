storage "raft" {
  path    = "/vault/data"
  node_id = "vault_1"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = "false"
  tls_cert_file = "/vault/tls/vault.crt"
  tls_key_file  = "/vault/tls/vault.key"
}

api_addr = "https://vault.maily.internal:8200"
cluster_addr = "https://vault.maily.internal:8201"

ui = true

telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Uncomment for AWS KMS auto-unseal
# seal "awskms" {
#   region     = "us-west-2"
#   kms_key_id = "alias/maily-vault-unseal"
# }
