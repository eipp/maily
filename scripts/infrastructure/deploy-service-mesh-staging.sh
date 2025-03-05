#!/bin/bash
set -euo pipefail

# Deploy Istio Service Mesh to Staging Environment
# This script installs Istio and deploys the service mesh configuration

echo "Deploying Istio Service Mesh to Staging Environment..."

# Set environment variables
NAMESPACE="staging"
ISTIO_VERSION="1.19.3"
MAILY_RELEASE="maily-staging"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "Error: helm is not installed"
    exit 1
fi

# Install Istio using Helm
echo "Installing Istio ${ISTIO_VERSION}..."

# Add Istio Helm repository if not already added
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Create Istio system namespace if it doesn't exist
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -

# Install Istio base
echo "Installing Istio base components..."
helm upgrade --install istio-base istio/base \
  --namespace istio-system \
  --version ${ISTIO_VERSION} \
  --wait

# Install Istio discovery (istiod)
echo "Installing Istio control plane (istiod)..."
helm upgrade --install istiod istio/istiod \
  --namespace istio-system \
  --version ${ISTIO_VERSION} \
  --wait

# Label the namespace for Istio injection
echo "Enabling automatic sidecar injection in ${NAMESPACE} namespace..."
kubectl label namespace ${NAMESPACE} istio-injection=enabled --overwrite

# Deploy Istio gateway
echo "Installing Istio gateway..."
helm upgrade --install istio-ingress istio/gateway \
  --namespace istio-system \
  --version ${ISTIO_VERSION} \
  --wait

# Apply Maily service mesh configuration
echo "Deploying Maily service mesh configuration..."
helm upgrade --install ${MAILY_RELEASE} ./infrastructure/helm/maily \
  --namespace ${NAMESPACE} \
  --values ./infrastructure/helm/maily/values-staging.yaml \
  --set global.istio.enabled=true \
  --wait

# Deploy Kiali dashboard for service mesh visualization
echo "Installing Kiali dashboard..."
helm repo add kiali https://kiali.org/helm-charts
helm repo update
helm upgrade --install kiali-server kiali/kiali-server \
  --namespace istio-system \
  --set auth.strategy=anonymous \
  --set deployment.ingress.enabled=true \
  --set deployment.ingress.class_name=istio \
  --wait

# Deploy Jaeger for distributed tracing
echo "Installing Jaeger for distributed tracing..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%.*}/samples/addons/jaeger.yaml -n istio-system

# Deploy Prometheus and Grafana for metrics and visualization
echo "Installing Prometheus and Grafana..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%.*}/samples/addons/prometheus.yaml -n istio-system
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%.*}/samples/addons/grafana.yaml -n istio-system

# Verify installation
echo "Verifying Istio installation..."
kubectl get pods -n istio-system

# Run tests to verify service mesh functionality
echo "Running service mesh validation tests..."
kubectl apply -f ./infrastructure/kubernetes/service-mesh/validation/test-deployment.yaml -n ${NAMESPACE}
sleep 10
kubectl exec -it $(kubectl get pod -l app=service-mesh-test -n ${NAMESPACE} -o jsonpath='{.items[0].metadata.name}') -n ${NAMESPACE} -- curl -s api-service:8000/health

echo "Service mesh deployment to staging complete!"
echo "Access the Kiali dashboard at: http://kiali.istio-system.svc:20001"
echo "Access the Grafana dashboard at: http://grafana.istio-system.svc:3000"