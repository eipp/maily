#!/bin/bash

# Install necessary packages
apt-get update
apt-get install -y unzip jq

# Install Vault
VAULT_VERSION="1.15.2"
curl -fsSL https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip -o vault.zip
unzip vault.zip
mv vault /usr/local/bin/
chmod +x /usr/local/bin/vault

# Create Vault user and directories
useradd --system --home /etc/vault --shell /bin/false vault
mkdir -p /etc/vault/data
chown -R vault:vault /etc/vault

# Create Vault configuration
cat > /etc/vault/config.hcl << EOF
ui = true

storage "file" {
  path = "/etc/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = "true"
}

seal "awskms" {
  region     = "${region}"
  kms_key_id = "${kms_key_id}"
}

api_addr = "http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8200"
EOF

# Create Vault systemd service
cat > /etc/systemd/system/vault.service << EOF
[Unit]
Description=Vault
Documentation=https://www.vaultproject.io/docs/
Requires=network-online.target
After=network-online.target

[Service]
User=vault
Group=vault
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=yes
PrivateDevices=yes
SecureBits=keep-caps
AmbientCapabilities=CAP_IPC_LOCK
Capabilities=CAP_IPC_LOCK+ep
CapabilityBoundingSet=CAP_SYSLOG CAP_IPC_LOCK
NoNewPrivileges=yes
ExecStart=/usr/local/bin/vault server -config=/etc/vault/config.hcl
ExecReload=/bin/kill --signal HUP \$MAINPID
KillMode=process
KillSignal=SIGINT
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitIntervalSec=60
StartLimitBurst=3
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Start Vault service
systemctl daemon-reload
systemctl enable vault
systemctl start vault

# Wait for Vault to start
sleep 10

# Initialize Vault
export VAULT_ADDR=http://127.0.0.1:8200
vault operator init -format=json > /etc/vault/init.json
chmod 600 /etc/vault/init.json

# Unseal Vault
cat /etc/vault/init.json | jq -r '.unseal_keys_b64[0]' | vault operator unseal -
cat /etc/vault/init.json | jq -r '.unseal_keys_b64[1]' | vault operator unseal -
cat /etc/vault/init.json | jq -r '.unseal_keys_b64[2]' | vault operator unseal -

# Set up Vault for Kubernetes
export VAULT_TOKEN=$(cat /etc/vault/init.json | jq -r '.root_token')

# Enable Kubernetes auth method
vault auth enable kubernetes

# Configure Kubernetes auth method
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc.cluster.local:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token

# Enable secrets engines
vault secrets enable -path=secret kv-v2
vault secrets enable transit

# Create policies
cat > /tmp/app-policy.hcl << EOF
path "secret/data/maily/*" {
  capabilities = ["read"]
}
EOF

vault policy write maily-app /tmp/app-policy.hcl

# Create Kubernetes role
vault write auth/kubernetes/role/maily-app \
  bound_service_account_names=maily-app \
  bound_service_account_namespaces=default \
  policies=maily-app \
  ttl=1h
