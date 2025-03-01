# Monitoring Policy

# Allow monitoring endpoints to be checked
path "sys/health" {
  capabilities = ["read", "sudo"]
}

# Allow reading telemetry data
path "sys/metrics" {
  capabilities = ["read"]
}

# Allow reading seal status
path "sys/seal-status" {
  capabilities = ["read"]
}

# Allow reading leader status
path "sys/leader" {
  capabilities = ["read"]
}

# Allow checking license status
path "sys/license/status" {
  capabilities = ["read"]
}
