# Maily Vault Production Setup

This directory contains configuration files and scripts for Maily's production Vault deployment.

## Components

- **Config**: Server configuration files
- **Scripts**: Initialization, backup, rotation, and maintenance scripts
- **Policies**: Access control policies for API services and monitoring
- **TLS**: Certificate generation and storage (certificates are not stored in Git)
- **Agent-Config**: Vault Agent configuration for dynamic secret delivery

## Setup Instructions

### Docker Compose Setup

1. Generate TLS certificates:
   ```
   ./vault/scripts/generate-tls-certs.sh
   ```

2. Start Vault in production mode:
   ```
   docker-compose -f docker-compose.production-vault.yml up -d
   ```

3. Initialize Vault:
   ```
   docker exec -it maily-vault-prod /vault/scripts/init-prod-vault.sh
   ```

4. Store the unseal keys and root token securely. **NEVER commit these to Git.**

### Kubernetes Setup

1. Apply the Kubernetes configurations:
   ```
   kubectl apply -f kubernetes/vault-deployment.yaml
   kubectl apply -f kubernetes/vault-agent-injector.yaml
   ```

2. Initialize Vault:
   ```
   kubectl exec -it vault-0 -n vault -- /vault/scripts/init-prod-vault.sh
   ```

3. Store the unseal keys and root token securely. **NEVER commit these to Git.**

## Migration from Development

To migrate from a development Vault to production:

```
export PROD_VAULT_TOKEN=your_production_vault_token
./vault/scripts/migrate-dev-to-prod.sh
```

## Maintenance

### Scheduled Maintenance

For Linux/systemd environments, use the provided service and timer files:

```
sudo cp vault/config/vault-maintenance.service /etc/systemd/system/
sudo cp vault/config/vault-maintenance.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vault-maintenance.timer
```

Alternatively, set up a cron job:

```
# Run vault maintenance daily at 2 AM
0 2 * * * VAULT_ADDR=https://vault.maily.internal:8200 VAULT_TOKEN=$(cat /etc/vault/token) /vault/scripts/vault-maintenance.sh
```

### Manual Maintenance

Run the maintenance script manually:

```
VAULT_ADDR=https://vault.maily.internal:8200 VAULT_TOKEN=your_token ./vault/scripts/vault-maintenance.sh
```

Use different actions:
- `backup`: Run backup only
- `rotate`: Rotate secrets only
- `cleanup`: Clean up tokens only
- `health`: Run health check only
- `all`: Run all tasks (default)

## Usage with Applications

### Direct API Access

Applications can access Vault directly using the hvac client:

```python
import hvac
client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
```

### Vault Agent Integration

1. Set up Vault Agent:
   ```
   # Write the role ID and secret ID to files
   echo "role-id" > vault/agent-config/role-id
   echo "secret-id" > vault/agent-config/secret-id
   ```

2. Configure the application to read from Vault Agent templates:
   ```
   export VAULT_AGENT_ENABLED=true
   export VAULT_AGENT_DB_FILE=/vault/agent-data/db-creds.json
   export VAULT_AGENT_REDIS_FILE=/vault/agent-data/redis-creds.json
   ```

### Kubernetes with Vault Agent Injector

Use annotations in pod specifications:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-inject-secret-db-creds.json: "database/creds/api-service"
  vault.hashicorp.com/agent-inject-template-db-creds.json: |
    {{ with secret "database/creds/api-service" -}}
    {
      "db": {
        "username": "{{ .Data.username }}",
        "password": "{{ .Data.password }}"
      }
    }
    {{- end }}
  vault.hashicorp.com/role: "api-service"
```

## Security Best Practices

1. **Unseal Keys**: Store unseal keys securely and distribute them to different trusted individuals
2. **Root Token**: Use the root token only for initial setup, then revoke it
3. **TLS**: Always use TLS in production
4. **Audit Logs**: Enable and monitor audit logs
5. **Backup**: Regularly back up Vault data
6. **Auto-Unseal**: Consider using AWS KMS auto-unseal in production
7. **Secret Rotation**: Implement regular secret rotation
8. **Monitoring**: Set up Prometheus alerts for Vault metrics

## Troubleshooting

- **Vault Sealed**: If Vault becomes sealed, unseal it using the unseal keys
- **Authentication Issues**: Check token validity and policy permissions
- **TLS Issues**: Verify that certificates are valid and trusted
