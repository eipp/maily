# Vault Integration Guide for Maily

This guide explains how to use the HashiCorp Vault integration for secret management in the Maily application. It's intended for developers who need to access or modify secrets in their code.

## Overview

Maily uses HashiCorp Vault for secret management, providing:

- Centralized secret storage and access control
- Dynamic secrets generation
- Automatic secret rotation
- Audit logging
- Enhanced security with encryption as a service

## Secret Structure

Secrets are organized in Vault using the following paths:

- `maily/data/config` - Core configuration (database, Redis, JWT, etc.)
- `maily/data/api-keys` - API keys for external services
- `maily/data/credentials` - Service credentials (AWS, etc.)

## Using the Vault Service in Python

### Basic Usage

```python
from apps.api.services.vault_service import vault_service

async def my_function():
    # Get a configuration value
    config = await vault_service.get_config()
    db_host = config.get("db_host")
    
    # Get credentials for a specific service
    aws_creds = await vault_service.get_credentials("aws")
    access_key = aws_creds.get("aws_access_key")
    
    # Get API keys
    api_keys = await vault_service.get_api_keys()
    stripe_key = api_keys.get("stripe")
```

### Registering a Secret Listener

```python
from apps.api.services.vault_service import vault_service

def my_config_callback(new_config):
    print(f"Configuration updated: {new_config}")
    # Update local settings

async def setup():
    # Register a callback for when the config changes
    await vault_service.register_secret_listener(
        "maily/data/config", my_config_callback
    )
```

### Using Encryption Service

```python
from apps.api.services.vault_service import vault_service

async def encrypt_sensitive_data(data):
    encrypted = await vault_service.encrypt_data("maily-enc-key", data)
    return encrypted

async def decrypt_sensitive_data(encrypted_data):
    decrypted = await vault_service.decrypt_data("maily-enc-key", encrypted_data)
    return decrypted
```

## Using Vault in TypeScript/JavaScript

For TypeScript/JavaScript services, we provide a Vault client that wraps the Vault API:

```typescript
import { getVaultClient } from '@maily/services/vault';

async function getSecrets() {
  const vaultClient = await getVaultClient();
  
  // Get configuration
  const config = await vaultClient.getSecret('maily/data/config');
  const dbHost = config.db_host;
  
  // Get API keys
  const apiKeys = await vaultClient.getSecret('maily/data/api-keys');
  const stripeKey = apiKeys.stripe;
}
```

## Accessing Vault in Kubernetes

Services running in Kubernetes can access Vault secrets through the Vault Agent Injector:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-service
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/agent-inject-secret-config.json: "maily/data/config"
        vault.hashicorp.com/role: "maily"
        vault.hashicorp.com/agent-inject-template-config.json: |
          {{ with secret "maily/data/config" }}
          {
            "database": {
              "host": "{{ .Data.data.db_host }}",
              "port": {{ .Data.data.db_port }},
              "username": "{{ .Data.data.db_username }}",
              "password": "{{ .Data.data.db_password }}"
            },
            "redis": {
              "host": "{{ .Data.data.redis_host }}",
              "port": {{ .Data.data.redis_port }},
              "password": "{{ .Data.data.redis_password }}"
            }
          }
          {{ end }}
```

This will inject the secrets as a file at `/vault/secrets/config.json` that your application can read.

## Secret Rotation

Secrets are automatically rotated based on their type:

| Secret Type | Default Rotation Interval | Production Interval |
|-------------|---------------------------|---------------------|
| Database    | 30 days                   | 30 days             |
| JWT         | 90 days                   | 90 days             |
| AWS         | 90 days                   | 90 days             |
| SMTP        | 180 days                  | 180 days            |
| API Keys    | 90 days                   | 90 days             |

Rotation happens automatically via a Kubernetes CronJob. If your service uses the Vault service with listeners registered, it will automatically pick up the new secrets when they change.

To manually rotate specific secrets, you can use the `mailyctl.py` script:

```bash
# To rotate a specific secret type
./mailyctl.py secrets rotate --secret-types=jwt,aws

# To rotate secrets for a specific environment
./mailyctl.py secrets rotate --env=production

# To rotate secrets and notify administrators
./mailyctl.py secrets rotate --env=production --notify
```

## Secret Management Best Practices

1. **Never hardcode secrets** in source code or configuration files.
2. **Use the Vault service** for all secret access - don't bypass it with direct API calls.
3. **Register secret listeners** to automatically respond to secret changes.
4. **Minimize secret access scope** by only requesting the specific secrets your service needs.
5. **Handle unavailability** of the Vault service gracefully (e.g., cache essential secrets locally).
6. **Log accesses** to sensitive secrets for audit purposes.
7. **Test with rotated secrets** to ensure your application handles secret rotation correctly.

## Troubleshooting

### Cannot Connect to Vault

If your service cannot connect to Vault:

1. Check that the Vault service is running: `kubectl get pods -n vault`
2. Verify that your service has the correct Vault address: `http://vault.vault:8200`
3. Ensure your service has appropriate authentication tokens or credentials
4. Check the Vault logs: `kubectl logs -n vault vault-0`

### Secret Not Found

If a secret is not found:

1. Verify the secret path is correct
2. Check if your service has permission to access the secret
3. Check if the secret exists in Vault using the Vault CLI or UI

### Secret Rotation Issues

If there are issues with secret rotation:

1. Check the rotation logs: `kubectl logs -n vault vault-secret-rotation-<pod-id>`
2. Verify the rotation configuration in the ConfigMap
3. Ensure the service has permissions to update services with the new secrets

## Additional Resources

- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [Kubernetes Vault Integration](https://www.vaultproject.io/docs/platform/k8s)
- [Vault API Reference](https://www.vaultproject.io/api-docs/)