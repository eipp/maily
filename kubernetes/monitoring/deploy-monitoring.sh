#!/bin/bash
set -e

# Function to replace VERSION placeholder
replace_version() {
    local file=$1
    local version=$2
    sed -i '' "s/VERSION/$version/g" "$file"
}

# Function to check if namespace exists
check_namespace() {
    if ! kubectl get namespace monitoring &> /dev/null; then
        echo "Creating monitoring namespace..."
        kubectl create namespace monitoring
    fi
}

# Function to deploy a manifest
deploy_manifest() {
    local file=$1
    local version=$2
    
    echo "Deploying $file..."
    cp "$file.template" "$file"
    replace_version "$file" "$version"
    kubectl apply -f "$file"
    rm "$file"
}

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    local timeout=300

    echo "Waiting for deployment $deployment to be ready..."
    kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment -n $namespace
}

# Main deployment function
deploy_monitoring() {
    local version=$1
    local grafana_password=$2

    if [ -z "$version" ] || [ -z "$grafana_password" ]; then
        echo "Usage: $0 <version> <grafana_password>"
        exit 1
    fi

    # Convert password to base64
    local encoded_password=$(echo -n "$grafana_password" | base64)

    # Ensure we're in the monitoring directory
    cd "$(dirname "$0")"

    # Check and create namespace if needed
    check_namespace

    # Deploy Prometheus
    deploy_manifest "prometheus-production.yaml" "$version"
    wait_for_deployment "prometheus" "monitoring"

    # Create Grafana secret
    cp "grafana-secret.yaml.template" "grafana-secret.yaml"
    sed -i '' "s/CHANGE_ME/$encoded_password/g" "grafana-secret.yaml"
    kubectl apply -f "grafana-secret.yaml"
    rm "grafana-secret.yaml"

    # Deploy Grafana
    deploy_manifest "grafana-production.yaml" "$version"
    wait_for_deployment "grafana" "monitoring"

    # Deploy Ingress
    deploy_manifest "ingress.yaml" "$version"

    echo "Monitoring stack deployment complete!"
    echo "Grafana will be available at https://your-alb-endpoint/grafana"
    echo "Prometheus will be available at https://your-alb-endpoint/prometheus"
    echo "Default username: admin"
    echo "Password: $grafana_password"
}

# Execute deployment
deploy_monitoring "$@" 