# Maily Helm Chart

This Helm chart deploys the Maily platform on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure
- Ingress controller (optional, but recommended)

## Getting Started

### Add the Helm repository

```bash
helm repo add maily https://helm.justmaily.com
helm repo update
```

### Installing the Chart

To install the chart with the release name `maily`:

```bash
# For development environment
helm install maily maily/maily -f values-development.yaml

# For staging environment
helm install maily maily/maily -f values-staging.yaml

# For production environment
helm install maily maily/maily -f values.yaml
```

This will deploy the Maily platform with the default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

### Upgrading the Chart

To upgrade the chart:

```bash
# For development environment
helm upgrade maily maily/maily -f values-development.yaml

# For staging environment
helm upgrade maily maily/maily -f values-staging.yaml

# For production environment
helm upgrade maily maily/maily -f values.yaml
```

## Configuration

This chart provides three different value files for different environments:

- `values-development.yaml`: Configuration for the development environment
- `values-staging.yaml`: Configuration for the staging environment
- `values.yaml`: Configuration for the production environment

## Parameters

The following tables list the configurable parameters of the Maily chart and their default values.

### Global Parameters

| Parameter                  | Description                                                | Default          |
|----------------------------|------------------------------------------------------------|------------------|
| `global.environment`       | Environment (development, staging, production)             | `production`     |
| `global.imageRegistry`     | Global Docker image registry                               | `ghcr.io/maily`  |
| `global.imagePullSecrets`  | Global Docker registry secret names as an array            | `[]`             |
| `global.storageClass`      | Global storage class for dynamic provisioning              | `standard`       |

### Service Mesh Configuration

| Parameter                                | Description                                         | Default                |
|------------------------------------------|-----------------------------------------------------|------------------------|
| `global.istio.enabled`                   | Enable Istio service mesh integration               | `true`                 |
| `global.istio.version`                   | Istio version to use                                | `1.19.3`               |
| `global.istio.gateway`                   | Istio gateway to use                                | `istio-system/maily-gateway` |
| `global.istio.mtls.mode`                 | mTLS mode for service-to-service communication      | `STRICT`               |
| `global.istio.mtls.defaultMode`          | Default mTLS mode for cross-namespace communication | `PERMISSIVE`           |
| `global.istio.timeout.api`               | Timeout for API service                             | `15s`                  |
| `global.istio.timeout.ai`                | Timeout for AI service                              | `30s`                  |
| `global.istio.timeout.email`             | Timeout for Email service                           | `20s`                  |
| `global.istio.retries.api.attempts`      | Number of retry attempts for API service            | `3`                    |
| `global.istio.retries.api.perTryTimeout` | Timeout per retry for API service                   | `2s`                   |
| `global.istio.canary.enabled`            | Enable canary deployments                           | `false`                |
| `global.istio.canary.weight`             | Traffic weight for canary version                   | `10`                   |

### Frontend Configuration

| Parameter                               | Description                                                | Default                  |
|-----------------------------------------|------------------------------------------------------------|--------------------------|
| `frontend.enabled`                      | Deploy frontend                                            | `true`                   |
| `frontend.replicaCount`                 | Number of frontend replicas                                | `3`                      |
| `frontend.image.repository`             | Frontend image name                                        | `maily-frontend`         |
| `frontend.image.tag`                    | Frontend image tag                                         | `latest`                 |
| `frontend.image.pullPolicy`             | Frontend image pull policy                                 | `Always`                 |
| `frontend.service.type`                 | Frontend service type                                      | `ClusterIP`              |
| `frontend.service.port`                 | Frontend service port                                      | `80`                     |
| `frontend.resources`                    | Frontend resource requests/limits                          | See values.yaml          |
| `frontend.autoscaling.enabled`          | Enable autoscaling for frontend                            | `true`                   |
| `frontend.autoscaling.minReplicas`      | Minimum number of frontend replicas                        | `3`                      |
| `frontend.autoscaling.maxReplicas`      | Maximum number of frontend replicas                        | `10`                     |

### Backend Configuration

| Parameter                               | Description                                                | Default                  |
|-----------------------------------------|------------------------------------------------------------|--------------------------|
| `backend.enabled`                       | Deploy backend                                             | `true`                   |
| `backend.replicaCount`                  | Number of backend replicas                                 | `3`                      |
| `backend.image.repository`              | Backend image name                                         | `maily-backend`          |
| `backend.image.tag`                     | Backend image tag                                          | `latest`                 |
| `backend.image.pullPolicy`              | Backend image pull policy                                  | `Always`                 |
| `backend.service.type`                  | Backend service type                                       | `ClusterIP`              |
| `backend.service.port`                  | Backend service port                                       | `80`                     |
| `backend.resources`                     | Backend resource requests/limits                           | See values.yaml          |
| `backend.autoscaling.enabled`           | Enable autoscaling for backend                             | `true`                   |
| `backend.autoscaling.minReplicas`       | Minimum number of backend replicas                         | `3`                      |
| `backend.autoscaling.maxReplicas`       | Maximum number of backend replicas                         | `10`                     |

## AI Service Configuration

| Parameter                               | Description                                                | Default                  |
|-----------------------------------------|------------------------------------------------------------|--------------------------|
| `aiService.enabled`                     | Deploy AI service                                          | `true`                   |
| `aiService.replicas`                    | Number of AI service replicas                              | `2`                      |
| `aiService.image.repository`            | AI service image name                                      | `ghcr.io/maily/ai-service` |
| `aiService.image.tag`                   | AI service image tag                                       | `latest`                 |
| `aiService.image.pullPolicy`            | AI service image pull policy                               | `Always`                 |
| `aiService.service.type`                | AI service service type                                    | `ClusterIP`              |
| `aiService.service.port`                | AI service service port                                    | `80`                     |
| `aiService.resources`                   | AI service resource requests/limits                        | See values.yaml          |
| `aiService.autoscaling.enabled`         | Enable autoscaling for AI service                          | `true`                   |
| `aiService.autoscaling.minReplicas`     | Minimum number of AI service replicas                      | `2`                      |
| `aiService.autoscaling.maxReplicas`     | Maximum number of AI service replicas                      | `10`                     |
| `aiService.memory.enabled`              | Enable memory for AI service                               | `true`                   |
| `aiService.memory.persistenceEnabled`   | Enable persistence for AI service memory                   | `true`                   |
| `aiService.memory.vectorStore`          | Vector store for AI service memory                         | `redis`                  |

## Automated Deployment Pipeline

### Phased Deployment Strategy

The Maily platform uses a phased deployment strategy to ensure a smooth rollout process:

1. **Phase 1: Staging Deployment**
   - Deployment to staging environment
   - Automated testing with E2E test suite
   - Performance validation with load testing
   - Approval gate (manual or automated)

2. **Phase 2: Production Canary**
   - Initial deployment to small subset of production nodes
   - Gradual traffic shifting (5%, 10%, 25%)
   - Continuous monitoring of error rates, latency, and resource usage
   - Approval gate (manual or automated)

3. **Phase 3: Full Production Rollout**
   - Complete rollout to all production nodes
   - Post-deployment verification
   - SLA monitoring activation

### Using the Deployment Scripts

The `maily-deploy.sh` script provides a standardized way to deploy across environments:

```bash
# Deploy to staging
./scripts/core/maily-deploy.sh --environment staging

# Deploy to production with full phase progression
./scripts/core/maily-deploy.sh --environment production

# Start at specific phase
./scripts/core/maily-deploy.sh --environment production --start-phase 2

# Skip verification steps (not recommended for production)
./scripts/core/maily-deploy.sh --environment staging --skip-verification

# Dry run mode to preview changes
./scripts/core/maily-deploy.sh --environment production --dry-run

# Deploy with service mesh
./scripts/core/maily-deploy.sh --environment staging --service-mesh-version 1.19.3

# Deploy as canary with service mesh
./scripts/core/maily-deploy.sh --environment production --canary --canary-weight 20

# Skip service mesh deployment
./scripts/core/maily-deploy.sh --environment staging --skip-service-mesh
```

### CI/CD Integration

This chart can be used with CI/CD systems like GitHub Actions:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
          
      - name: Update kubeconfig
        run: aws eks update-kubeconfig --name maily-${{ env.ENVIRONMENT }} --region us-west-2
        
      - name: Deploy with phased strategy
        run: |
          ./scripts/core/maily-deploy.sh \
            --environment ${{ env.ENVIRONMENT }} \
            --version ${{ github.sha }} \
            --notify slack
        env:
          ENVIRONMENT: ${{ github.event.inputs.environment || 'staging' }}
```

### Deployment Monitoring and Rollback

The deployment process includes built-in monitoring and automatic rollback:

```bash
# Monitor a deployment
./scripts/core/maily-deploy.sh --environment production --monitor-only

# Rollback a failed deployment
./scripts/utils/automated-rollback.sh --environment production --version previous
```

## Troubleshooting

If you encounter issues with your deployment, you can get more information about the chart installation with:

```bash
helm list
helm status maily
kubectl get pods -l app.kubernetes.io/instance=maily
```

For more details, check the logs of the specific component:

```bash
kubectl logs -l app.kubernetes.io/name=maily-frontend -f
kubectl logs -l app.kubernetes.io/name=maily-backend -f
kubectl logs -l app.kubernetes.io/name=maily-ai-service -f
```