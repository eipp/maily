# Maily Kubernetes Infrastructure

This directory contains Kubernetes configurations for deploying and scaling the Maily application.

## Configuration Files

This directory contains various Kubernetes manifests for deploying the entire Maily infrastructure:

- Base deployments (backend, frontend, workers)
- Database and caching services
- Security components
- Monitoring and observability
- Backup and disaster recovery

## Deployment Instructions

### Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured to communicate with your cluster
- Docker registry with the Maily images
- Prometheus Operator installed in the cluster
- cert-manager installed for TLS certificate management

### Configuration

Before deploying, you need to create the necessary ConfigMap and Secret resources:

```bash
# Create ConfigMap with non-sensitive configuration
kubectl create configmap maily-config \
  --from-literal=REDIS_URL=redis://redis:6379/0 \
  --from-literal=SUPABASE_URL=https://your-supabase-project.supabase.co

# Create Secret with sensitive configuration
kubectl create secret generic maily-secrets \
  --from-literal=SUPABASE_KEY=your-supabase-key \
  --from-literal=OPENAI_API_KEY=your-openai-api-key \
  --from-literal=ANTHROPIC_API_KEY=your-anthropic-api-key \
  --from-literal=GOOGLE_API_KEY=your-google-api-key \
  --from-literal=JWT_SECRET=your-jwt-secret
```

### Deployment

Deploy the application using kubectl:

```bash
# Deploy the entire infrastructure
kubectl apply -f infrastructure/kubernetes/

# Deploy specific components
kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/
```

### Scaling

The deployments are configured with initial settings for scaling:

- Initial replicas: 3
- CPU requests: 500m (0.5 CPU cores)
- CPU limits: 1 CPU core
- Memory requests: 1Gi
- Memory limits: 2Gi

For automatic scaling, you can add a Horizontal Pod Autoscaler:

```bash
kubectl autoscale deployment maily-api --cpu-percent=70 --min=3 --max=10
```

This will automatically scale the deployment between 3 and 10 replicas based on CPU utilization.

## Monitoring and Alerting

The monitoring directory sets up:

1. ServiceMonitors to scrape metrics from all services
2. PrometheusRules for alerting on:
   - High error rates (>5% for 5 minutes)
   - High API latency (95th percentile >2s for 5 minutes)
   - Database performance issues
   - Redis cache issues

To view the Prometheus dashboard, forward the port:

```bash
kubectl port-forward svc/prometheus-operated 9090:9090
```

To view the Grafana dashboard (if installed):

```bash
kubectl port-forward svc/grafana 3000:3000
```

## Security Components

This directory includes security-related components:

- OPA (Open Policy Agent) for policy enforcement
- Vault for secrets management
- Kyverno for policy management
- Network policies for secure communication

## Production Considerations

For production deployments, consider:

1. Setting up proper network policies
2. Configuring pod disruption budgets
3. Implementing proper backup and restore procedures
4. Setting up multi-region deployments for high availability
5. Implementing proper logging and monitoring solutions
6. Setting up proper CI/CD pipelines for automated deployments
