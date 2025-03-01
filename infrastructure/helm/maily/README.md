# Maily Helm Chart

This Helm chart deploys the Maily email marketing platform on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure
- LoadBalancer support or Ingress Controller installed

## Getting Started

### Add the Maily Helm repository

```bash
helm repo add maily https://maily.github.io/helm-charts
helm repo update
```

### Install the chart

```bash
# Install with default values
helm install maily maily/maily

# Install with custom values file
helm install maily maily/maily -f values.yaml

# Install in a specific namespace
helm install maily maily/maily --namespace maily --create-namespace
```

## Configuration

The following table lists the configurable parameters of the Maily chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Environment name | `production` |
| `global.imageRegistry` | Global Docker image registry | `ghcr.io/maily` |
| `global.imagePullSecrets` | Global Docker registry secret names as an array | `[]` |
| `global.storageClass` | Global StorageClass for Persistent Volume(s) | `standard` |

### Frontend Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `frontend.enabled` | Enable frontend deployment | `true` |
| `frontend.replicaCount` | Number of frontend replicas | `3` |
| `frontend.image.repository` | Frontend image repository | `maily-frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `frontend.image.pullPolicy` | Frontend image pull policy | `Always` |
| `frontend.service.type` | Frontend service type | `ClusterIP` |
| `frontend.service.port` | Frontend service port | `80` |
| `frontend.service.targetPort` | Frontend container port | `3000` |
| `frontend.resources` | Frontend resource requests/limits | See `values.yaml` |
| `frontend.autoscaling.enabled` | Enable autoscaling for frontend | `true` |
| `frontend.autoscaling.minReplicas` | Minimum number of frontend replicas | `3` |
| `frontend.autoscaling.maxReplicas` | Maximum number of frontend replicas | `10` |
| `frontend.env` | Environment variables for frontend | See `values.yaml` |

### Backend Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable backend deployment | `true` |
| `backend.replicaCount` | Number of backend replicas | `3` |
| `backend.image.repository` | Backend image repository | `maily-backend` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.image.pullPolicy` | Backend image pull policy | `Always` |
| `backend.service.type` | Backend service type | `ClusterIP` |
| `backend.service.port` | Backend service port | `80` |
| `backend.service.targetPort` | Backend container port | `8000` |
| `backend.resources` | Backend resource requests/limits | See `values.yaml` |
| `backend.autoscaling.enabled` | Enable autoscaling for backend | `true` |
| `backend.autoscaling.minReplicas` | Minimum number of backend replicas | `3` |
| `backend.autoscaling.maxReplicas` | Maximum number of backend replicas | `10` |
| `backend.livenessProbe` | Liveness probe configuration | See `values.yaml` |
| `backend.readinessProbe` | Readiness probe configuration | See `values.yaml` |

### Worker Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `worker.enabled` | Enable worker deployment | `true` |
| `worker.replicaCount` | Number of worker replicas | `3` |
| `worker.image.repository` | Worker image repository | `maily-backend` |
| `worker.image.tag` | Worker image tag | `latest` |
| `worker.image.pullPolicy` | Worker image pull policy | `Always` |
| `worker.resources` | Worker resource requests/limits | See `values.yaml` |
| `worker.autoscaling.enabled` | Enable autoscaling for worker | `true` |
| `worker.autoscaling.minReplicas` | Minimum number of worker replicas | `3` |
| `worker.autoscaling.maxReplicas` | Maximum number of worker replicas | `10` |
| `worker.command` | Command to run in the worker container | `["python", "-m", "workers.email_worker"]` |

### PostgreSQL Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL deployment | `true` |
| `postgresql.image.repository` | PostgreSQL image repository | `postgres` |
| `postgresql.image.tag` | PostgreSQL image tag | `15-alpine` |
| `postgresql.service.port` | PostgreSQL service port | `5432` |
| `postgresql.persistence.enabled` | Enable persistence for PostgreSQL | `true` |
| `postgresql.persistence.size` | PostgreSQL PVC size | `10Gi` |
| `postgresql.resources` | PostgreSQL resource requests/limits | See `values.yaml` |
| `postgresql.env` | Environment variables for PostgreSQL | See `values.yaml` |

### Redis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis deployment | `true` |
| `redis.image.repository` | Redis image repository | `redis` |
| `redis.image.tag` | Redis image tag | `7-alpine` |
| `redis.service.port` | Redis service port | `6379` |
| `redis.persistence.enabled` | Enable persistence for Redis | `true` |
| `redis.persistence.size` | Redis PVC size | `5Gi` |
| `redis.resources` | Redis resource requests/limits | See `values.yaml` |

### RabbitMQ Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `rabbitmq.enabled` | Enable RabbitMQ deployment | `true` |
| `rabbitmq.image.repository` | RabbitMQ image repository | `rabbitmq` |
| `rabbitmq.image.tag` | RabbitMQ image tag | `3.12-management-alpine` |
| `rabbitmq.service.port` | RabbitMQ AMQP port | `5672` |
| `rabbitmq.service.managementPort` | RabbitMQ management port | `15672` |
| `rabbitmq.persistence.enabled` | Enable persistence for RabbitMQ | `true` |
| `rabbitmq.persistence.size` | RabbitMQ PVC size | `5Gi` |
| `rabbitmq.resources` | RabbitMQ resource requests/limits | See `values.yaml` |
| `rabbitmq.env` | Environment variables for RabbitMQ | See `values.yaml` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.annotations` | Ingress annotations | See `values.yaml` |
| `ingress.hosts` | Ingress hosts configuration | See `values.yaml` |
| `ingress.tls` | Ingress TLS configuration | See `values.yaml` |

### Secrets Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `secrets.create` | Create Kubernetes secrets | `true` |
| `secrets.name` | Name of the secret | `maily-secrets` |
| `secrets.data` | Secret data | See `values.yaml` |

## Upgrading

### To upgrade the release

```bash
helm upgrade maily maily/maily
```

### To rollback to a previous release

```bash
helm rollback maily [REVISION]
```

## Uninstalling the Chart

To uninstall/delete the `maily` deployment:

```bash
helm uninstall maily
```

This removes all the Kubernetes components associated with the chart and deletes the release.

## Persistence

The chart mounts persistent volumes for PostgreSQL, Redis, and RabbitMQ. The volumes are created using dynamic volume provisioning. If you want to disable persistence, set `*.persistence.enabled` to `false` for each component.

## Security

For production environments, make sure to:

1. Set strong passwords in the secrets section
2. Enable TLS for ingress
3. Use a private Docker registry with authentication
4. Consider using external managed services for PostgreSQL, Redis, and RabbitMQ

## Troubleshooting

### Check the status of the release

```bash
helm status maily
```

### Debug templates

```bash
helm template maily/maily --debug
```

### Get logs from pods

```bash
kubectl logs -f deployment/maily-backend
kubectl logs -f deployment/maily-frontend
kubectl logs -f deployment/maily-worker
```
