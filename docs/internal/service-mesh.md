# Service Mesh Implementation

This document describes the service mesh implementation for the Maily platform.

## Overview

Maily uses Istio as a service mesh to provide:

- **Traffic Management**: Control traffic flows and API calls between services
- **Security**: Mutual TLS encryption and service-to-service authentication
- **Observability**: Monitoring, logging, and tracing of service communications
- **Resilience**: Circuit breaking, retries, and timeouts for fault tolerance

## Architecture

The service mesh implementation follows this architecture:

```
                    ┌─────────────────────┐
                    │    Istio Ingress    │
                    │      Gateway        │
                    └──────────┬──────────┘
                               │
                               ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│              │     │                  │     │              │
│  Web Service ◄─────►    API Service   ◄─────►  AI Service  │
│              │     │                  │     │              │
└──────────────┘     └─────────┬────────┘     └──────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │                  │
                     │  Email Service   │
                     │                  │
                     └──────────────────┘
```

Each service has an Istio sidecar proxy (Envoy) that intercepts all inbound and outbound traffic, enabling the service mesh capabilities.

## Mutual TLS

All service-to-service communication is secured with mutual TLS. This provides:

- **Encryption**: All traffic is encrypted in transit
- **Authentication**: Services can only communicate if they have valid certificates
- **Authorization**: Fine-grained control over which services can communicate

Configuration is defined in `infrastructure/helm/maily/templates/mtls-policy.yaml`:

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: {{ include "maily.fullname" . }}-mtls-policy
  namespace: {{ .Release.Namespace }}
spec:
  mtls:
    mode: STRICT
```

## Circuit Breakers

Circuit breakers prevent cascading failures by limiting the impact of service failures:

- **Connection Limits**: Maximum number of connections to a service
- **Request Limits**: Maximum number of pending requests
- **Outlier Detection**: Automatic ejection of failing endpoints

Configuration is defined in `infrastructure/helm/maily/templates/circuit-breaker.yaml`.

## Traffic Management

Traffic management capabilities include:

- **Request Routing**: Control traffic distribution between services
- **Retry Policies**: Automatically retry failed requests
- **Timeout Control**: Set timeouts for service-to-service requests
- **Fault Injection**: Test resilience with simulated faults (in testing environments)

Configuration is defined in `infrastructure/helm/maily/templates/virtual-service.yaml`.

## Canary Deployments

Canary deployments allow gradual rollout of new versions:

1. Deploy new version alongside existing version
2. Route a small percentage of traffic to the new version (e.g., 10%)
3. Monitor for errors or performance issues
4. Gradually increase traffic to the new version
5. Complete the rollout when the new version is proven stable

Configuration is defined in the `canary` section of the virtual service configuration.

## Observability

The service mesh provides comprehensive observability:

- **Metrics**: Prometheus metrics for all service-to-service communications
- **Dashboards**: Grafana dashboards for service mesh monitoring
- **Distributed Tracing**: Jaeger for end-to-end request tracing

Custom dashboards are defined in `kubernetes/monitoring/grafana-service-mesh-dashboard.json`.

## Deployment

### Installation

The service mesh is installed using Helm and is managed by the `mailyctl.py` script:

```bash
# Deploy service mesh to staging
./mailyctl.py phased-deploy --env=staging --service-mesh-version=1.19.3

# Verify service mesh configuration
./mailyctl.py verify-mesh --env=staging --component=api
```

### Testing

A comprehensive test suite for the service mesh is available in `tests/integration/test_service_mesh_integration.py`. This includes tests for:

- Service health checks
- Service-to-service communication
- Circuit breaker functionality
- Retry policy verification
- mTLS verification
- Canary deployment routing
- Timeout functionality

Run the tests with:

```bash
pytest -xvs tests/integration/test_service_mesh_integration.py
```

## Configuration

### Helm Values

Service mesh configuration is defined in the `global.istio` section of the Helm values files:

- `values.yaml`: Production configuration
- `values-staging.yaml`: Staging configuration
- `values-development.yaml`: Development configuration

Parameters include:

- `enabled`: Enable/disable service mesh
- `version`: Istio version
- `mtls.mode`: mTLS mode (STRICT, PERMISSIVE, DISABLE)
- `timeout.*`: Timeouts for different services
- `retries.*`: Retry configurations
- `circuitBreaker.*`: Circuit breaker configurations
- `canary.*`: Canary deployment configurations

### Example Configuration

```yaml
global:
  istio:
    enabled: true
    version: "1.19.3"
    mtls:
      mode: "STRICT"
      defaultMode: "PERMISSIVE"
    timeout:
      api: "15s"
      ai: "30s"
      email: "20s"
    retries:
      api:
        attempts: 3
        perTryTimeout: "2s"
        retryOn: "connect-failure,refused-stream,gateway-error,5xx"
    circuitBreaker:
      api:
        maxConnections: 100
        consecutive5xxErrors: 5
    canary:
      enabled: false
      weight: 10
```

## Troubleshooting

### Common Issues

1. **Sidecar Injection Failures**:
   - Check namespace label: `kubectl get namespace <namespace> --show-labels`
   - Ensure `istio-injection=enabled` label is present

2. **mTLS Connection Issues**:
   - Check authentication policy: `kubectl get peerauthentication -n <namespace>`
   - Check for TLS errors in Envoy logs: `kubectl logs <pod-name> -c istio-proxy`

3. **Circuit Breaker Errors**:
   - Check destination rules: `kubectl get destinationrule -n <namespace>`
   - Check Envoy circuit breaker stats: `kubectl exec <pod-name> -c istio-proxy -- pilot-agent request GET stats | grep circuit_breakers`

### Debugging Commands

```bash
# Get Istio version
istioctl version

# Verify configuration
istioctl analyze -n <namespace>

# Check proxy status
istioctl proxy-status

# Get proxy configuration
istioctl proxy-config all <pod-name>.<namespace>

# Get virtual services
kubectl get virtualservices -n <namespace>

# Get destination rules
kubectl get destinationrules -n <namespace>
```

## References

- [Istio Documentation](https://istio.io/latest/docs/)
- [Envoy Documentation](https://www.envoyproxy.io/docs/envoy/latest/)
- [Helm Chart README](../../infrastructure/helm/maily/README.md)
- [Deployment Script](../../scripts/infrastructure/deploy-service-mesh-staging.sh)