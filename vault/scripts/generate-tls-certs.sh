#!/bin/bash
set -e

TLS_DIR="/vault/tls"
mkdir -p "$TLS_DIR"

# Generate CA key and certificate
echo "Generating CA key and certificate..."
openssl genrsa -out "$TLS_DIR/ca.key" 4096
openssl req -x509 -new -nodes -key "$TLS_DIR/ca.key" -sha256 -days 365 -out "$TLS_DIR/ca.crt" \
  -subj "/C=US/ST=California/L=San Francisco/O=Maily/OU=DevOps/CN=maily.ca"

# Generate Vault key and CSR
echo "Generating Vault key and CSR..."
openssl genrsa -out "$TLS_DIR/vault.key" 2048
openssl req -new -key "$TLS_DIR/vault.key" -out "$TLS_DIR/vault.csr" \
  -subj "/C=US/ST=California/L=San Francisco/O=Maily/OU=DevOps/CN=vault.maily.internal"

# Create a config file for the SAN extension
cat > "$TLS_DIR/vault_cert_ext.cnf" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = vault.maily.internal
DNS.2 = vault
DNS.3 = localhost
IP.1 = 127.0.0.1
EOF

# Sign the Vault CSR with our CA
echo "Signing Vault CSR with CA..."
openssl x509 -req -in "$TLS_DIR/vault.csr" -CA "$TLS_DIR/ca.crt" \
  -CAkey "$TLS_DIR/ca.key" -CAcreateserial -out "$TLS_DIR/vault.crt" \
  -days 365 -sha256 -extfile "$TLS_DIR/vault_cert_ext.cnf"

# Set appropriate permissions
echo "Setting appropriate permissions..."
chmod 600 "$TLS_DIR/ca.key"
chmod 600 "$TLS_DIR/vault.key"
chmod 644 "$TLS_DIR/ca.crt"
chmod 644 "$TLS_DIR/vault.crt"

echo "TLS certificates generated successfully!"
echo "  - CA certificate: $TLS_DIR/ca.crt"
echo "  - Vault certificate: $TLS_DIR/vault.crt"
echo "  - Vault key: $TLS_DIR/vault.key"
