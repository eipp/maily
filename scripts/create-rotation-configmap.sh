#!/bin/bash
# Script to create ConfigMap from the secret rotation script file

set -e

SECRET_ROTATION_SCRIPT="scripts/secret-rotation.sh"
NAMESPACE="maily-production"

# Check if file exists
if [ ! -f "$SECRET_ROTATION_SCRIPT" ]; then
    echo "Error: Script file not found at $SECRET_ROTATION_SCRIPT"
    exit 1
fi

# Create ConfigMap from script file
echo "Creating ConfigMap from $SECRET_ROTATION_SCRIPT..."
kubectl create configmap secret-rotation-scripts \
    --namespace "$NAMESPACE" \
    --from-file=secret-rotation.sh="$SECRET_ROTATION_SCRIPT" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "ConfigMap created successfully."
