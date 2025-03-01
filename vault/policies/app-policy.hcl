# API Service Policy

# Allow API service to read database credentials
path "database/creds/api-service" {
  capabilities = ["read"]
}

# Allow reading and listing of secrets
path "secret/data/api/*" {
  capabilities = ["read", "list"]
}

# Allow reading Redis secrets
path "secret/data/redis" {
  capabilities = ["read"]
}

# Allow transit operations for data encryption/decryption
path "transit/encrypt/maily-data*" {
  capabilities = ["update"]
}

path "transit/decrypt/maily-data*" {
  capabilities = ["update"]
}

# Allow renewing leases
path "sys/leases/renew" {
  capabilities = ["update"]
}

# Allow looking up lease information
path "sys/leases/lookup" {
  capabilities = ["update"]
}
