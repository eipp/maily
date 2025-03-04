# Secret Rotation Runbook

**Status**: 🧑‍💻 Partially Automated  
**Owner**: DevOps Team  
**Last Updated**: April 3, 2025  

## Overview

This runbook describes the process for rotating secrets across the Maily platform. Regular secret rotation is a security best practice that helps limit the risk exposure from compromised credentials.

## Prerequisites

- Access to Vault
- Kubernetes cluster access
- AWS CLI configured with appropriate permissions
- Understanding of the services that use the secrets being rotated

## Schedule

| Secret Type | Rotation Frequency | Automated |
|-------------|-------------------|-----------|
| Database credentials | Monthly | Yes |
| API keys (external services) | Quarterly | Partial |
| JWT signing keys | Bi-annually | Yes |
| Cloud provider credentials | Quarterly | No |
| Redis credentials | Monthly | Yes |
| LLM API keys | Quarterly | Yes |

## Automated Secret Rotation Process

The majority of our secret rotation is automated using Vault and Kubernetes CronJobs:

1. A weekly CronJob runs every Sunday at midnight to rotate configured secrets
2. The job pulls the rotation script from a ConfigMap
3. Each type of secret is rotated according to its own process
4. Services are updated with new credentials (via restart or dynamic reloading)
5. The job logs all operations to a PersistentVolume for auditing

### Viewing the Automated Rotation Schedule

```bash
# View the secret rotation CronJob
kubectl get cronjob secret-rotation -n maily-production

# View the most recent rotation job
kubectl get jobs -n maily-production | grep secret-rotation

# Check logs from the most recent rotation job
kubectl logs $(kubectl get pods -n maily-production -l job-name=secret-rotation-<job-id> -o name) -n maily-production
```

### Secret Rotation ConfigMap

The secret rotation script is stored in a ConfigMap. To update the script:

```bash
# View the current script
kubectl get configmap secret-rotation-scripts -n maily-production -o yaml

# Update the script from the file
scripts/create-rotation-configmap.sh
```

## Manual Secret Rotation Process

For secrets that are not automated or when manual rotation is needed:

### Database Credentials

1. Connect to Vault:
   ```bash
   export VAULT_ADDR=https://vault.vault.svc.cluster.local:8200
   vault login
   ```

2. Rotate database credentials for a specific role:
   ```bash
   # Get new credentials
   vault read database/creds/api-service
   
   # Update Kubernetes secret
   kubectl create secret generic db-credentials-api-service \
       --namespace maily-production \
       --from-literal=username="<new-username>" \
       --from-literal=password="<new-password>" \
       --dry-run=client -o yaml | kubectl apply -f -
   ```

3. Restart the affected service:
   ```bash
   kubectl rollout restart deployment api -n maily-production
   ```

4. Verify the service is functioning correctly:
   ```bash
   kubectl rollout status deployment api -n maily-production
   curl -s -o /dev/null -w "%{http_code}" https://api.mailyapp.com/health
   ```

### API Keys for External Services

1. Generate a new API key in the external service's dashboard.
2. Store the new key in Vault:
   ```bash
   vault kv put secret/api/sendgrid api_key="<new-api-key>"
   ```
3. Update the Kubernetes secret:
   ```bash
   kubectl create secret generic sendgrid-credentials \
       --namespace maily-production \
       --from-literal=api_key="<new-api-key>" \
       --dry-run=client -o yaml | kubectl apply -f -
   ```
4. Restart the affected services:
   ```bash
   kubectl rollout restart deployment email-service -n maily-production
   ```
5. Verify the service is functioning correctly:
   ```bash
   # Test sending an email
   curl -X POST https://api.mailyapp.com/v1/email/test \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"to":"test@example.com","subject":"Test Email","body":"This is a test"}'
   ```

### AWS Credentials

1. Create a new access key in AWS IAM Console for the service user
2. Store the new credentials in Vault:
   ```bash
   vault kv put secret/api/aws access_key="<new-access-key>" secret_key="<new-secret-key>"
   ```
3. Update the Kubernetes secret:
   ```bash
   kubectl create secret generic aws-credentials \
       --namespace maily-production \
       --from-literal=access_key="<new-access-key>" \
       --from-literal=secret_key="<new-secret-key>" \
       --dry-run=client -o yaml | kubectl apply -f -
   ```
4. Revoke the old access key after confirming the new one works

## Running Manual Rotation for All Secrets

To manually trigger a full secret rotation:

```bash
# Update the ConfigMap with the latest script
scripts/create-rotation-configmap.sh

# Create a manual job from the CronJob
kubectl create job --from=cronjob/secret-rotation manual-secret-rotation-$(date +%s) -n maily-production

# Monitor the job
kubectl get job manual-secret-rotation-* -n maily-production
kubectl logs -f jobs/manual-secret-rotation-* -n maily-production
```

## Troubleshooting

### Failed Rotation Job

If the automatic rotation job fails:

1. Check the job logs for specific errors:
   ```bash
   kubectl logs $(kubectl get pods -n maily-production -l job-name=secret-rotation-<job-id> -o name) -n maily-production
   ```

2. Check Vault connectivity:
   ```bash
   kubectl exec -it $(kubectl get pods -n maily-production | grep vault-auth | head -1 | awk '{print $1}') -n maily-production -- vault status
   ```

3. Verify the Vault token is valid:
   ```bash
   kubectl describe secret vault-token -n maily-production
   ```

4. Check for service disruptions after rotation:
   ```bash
   kubectl get pods -n maily-production
   kubectl logs deployment/api -n maily-production | grep -i error
   ```

### Service Cannot Access Rotated Secrets

If a service cannot access the newly rotated secrets:

1. Verify the secret was actually updated:
   ```bash
   kubectl get secret <secret-name> -n maily-production -o yaml
   ```

2. Check if the service was restarted:
   ```bash
   kubectl describe pod <pod-name> -n maily-production | grep "Start Time"
   ```

3. Check for error logs from the service:
   ```bash
   kubectl logs <pod-name> -n maily-production
   ```

4. Manually restart the service if needed:
   ```bash
   kubectl rollout restart deployment <deployment-name> -n maily-production
   ```

## Related Alerts

- `VaultTokenExpiringSoon`: Vault token is nearing expiration
- `SecretRotationJobFailed`: Automated secret rotation job failed
- `ServiceAuthenticationFailure`: Service fails to authenticate with external service after rotation

## Metrics to Monitor

- `secret_rotation_job_duration_seconds`: Duration of the secret rotation job
- `secret_rotation_success_rate`: Percentage of successfully rotated secrets
- `authentication_failures_count`: Count of authentication failures per service
