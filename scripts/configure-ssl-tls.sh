#!/bin/bash
# configure-ssl-tls.sh
# Script to configure SSL/TLS for Maily

set -e

# Default values
DOMAIN="maily.com"
ENVIRONMENT="production"
USE_LETS_ENCRYPT=true
CERTIFICATE_PATH=""
PRIVATE_KEY_PATH=""
CHAIN_PATH=""
CLOUDFLARE_API_TOKEN=""
DNS_PROVIDER="cloudflare"
KUBERNETES_NAMESPACE="default"
INGRESS_NAME="maily-ingress"
MIN_TLS_VERSION="1.2"
CIPHERS="ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384"
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=true
OCSP_STAPLING=true
CERT_MANAGER_VERSION="v1.12.0"
CERT_MANAGER_NAMESPACE="cert-manager"
FORCE_RENEWAL=false
STAGING=false
EMAIL="admin@maily.com"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --use-lets-encrypt)
      USE_LETS_ENCRYPT="$2"
      shift 2
      ;;
    --certificate-path)
      CERTIFICATE_PATH="$2"
      shift 2
      ;;
    --private-key-path)
      PRIVATE_KEY_PATH="$2"
      shift 2
      ;;
    --chain-path)
      CHAIN_PATH="$2"
      shift 2
      ;;
    --cloudflare-api-token)
      CLOUDFLARE_API_TOKEN="$2"
      shift 2
      ;;
    --dns-provider)
      DNS_PROVIDER="$2"
      shift 2
      ;;
    --kubernetes-namespace)
      KUBERNETES_NAMESPACE="$2"
      shift 2
      ;;
    --ingress-name)
      INGRESS_NAME="$2"
      shift 2
      ;;
    --min-tls-version)
      MIN_TLS_VERSION="$2"
      shift 2
      ;;
    --ciphers)
      CIPHERS="$2"
      shift 2
      ;;
    --hsts-enabled)
      HSTS_ENABLED="$2"
      shift 2
      ;;
    --hsts-max-age)
      HSTS_MAX_AGE="$2"
      shift 2
      ;;
    --hsts-include-subdomains)
      HSTS_INCLUDE_SUBDOMAINS="$2"
      shift 2
      ;;
    --hsts-preload)
      HSTS_PRELOAD="$2"
      shift 2
      ;;
    --ocsp-stapling)
      OCSP_STAPLING="$2"
      shift 2
      ;;
    --cert-manager-version)
      CERT_MANAGER_VERSION="$2"
      shift 2
      ;;
    --cert-manager-namespace)
      CERT_MANAGER_NAMESPACE="$2"
      shift 2
      ;;
    --force-renewal)
      FORCE_RENEWAL="$2"
      shift 2
      ;;
    --staging)
      STAGING="$2"
      shift 2
      ;;
    --email)
      EMAIL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
  echo "Error: kubectl is not installed. Please install it first."
  exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
  echo "Error: helm is not installed. Please install it first."
  exit 1
fi

# Function to install cert-manager
install_cert_manager() {
  echo "Installing cert-manager version $CERT_MANAGER_VERSION..."
  
  # Create namespace for cert-manager
  kubectl create namespace "$CERT_MANAGER_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
  
  # Add Jetstack Helm repository
  helm repo add jetstack https://charts.jetstack.io
  helm repo update
  
  # Install cert-manager with CRDs
  helm upgrade --install cert-manager jetstack/cert-manager \
    --namespace "$CERT_MANAGER_NAMESPACE" \
    --version "$CERT_MANAGER_VERSION" \
    --set installCRDs=true \
    --set global.leaderElection.namespace="$CERT_MANAGER_NAMESPACE"
  
  # Wait for cert-manager to be ready
  kubectl -n "$CERT_MANAGER_NAMESPACE" rollout status deployment/cert-manager
  kubectl -n "$CERT_MANAGER_NAMESPACE" rollout status deployment/cert-manager-webhook
  kubectl -n "$CERT_MANAGER_NAMESPACE" rollout status deployment/cert-manager-cainjector
  
  echo "cert-manager installed successfully."
}

# Function to create ClusterIssuer for Let's Encrypt
create_cluster_issuer() {
  local issuer_name="letsencrypt-$ENVIRONMENT"
  local server="https://acme-v02.api.letsencrypt.org/directory"
  
  if [ "$STAGING" = true ]; then
    issuer_name="letsencrypt-staging"
    server="https://acme-staging-v02.api.letsencrypt.org/directory"
  fi
  
  echo "Creating ClusterIssuer $issuer_name..."
  
  # Create secret for DNS provider API token
  if [ "$DNS_PROVIDER" = "cloudflare" ] && [ -n "$CLOUDFLARE_API_TOKEN" ]; then
    kubectl create secret generic cloudflare-api-token \
      --namespace "$CERT_MANAGER_NAMESPACE" \
      --from-literal=api-token="$CLOUDFLARE_API_TOKEN" \
      --dry-run=client -o yaml | kubectl apply -f -
  fi
  
  # Create ClusterIssuer manifest
  cat > /tmp/cluster-issuer.yaml << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: $issuer_name
spec:
  acme:
    server: $server
    email: $EMAIL
    privateKeySecretRef:
      name: $issuer_name-account-key
    solvers:
EOF
  
  # Add DNS01 solver if using Cloudflare
  if [ "$DNS_PROVIDER" = "cloudflare" ] && [ -n "$CLOUDFLARE_API_TOKEN" ]; then
    cat >> /tmp/cluster-issuer.yaml << EOF
    - dns01:
        cloudflare:
          apiTokenSecretRef:
            name: cloudflare-api-token
            key: api-token
EOF
  else
    # Default to HTTP01 solver
    cat >> /tmp/cluster-issuer.yaml << EOF
    - http01:
        ingress:
          class: nginx
EOF
  fi
  
  # Apply ClusterIssuer
  kubectl apply -f /tmp/cluster-issuer.yaml
  
  # Wait for ClusterIssuer to be ready
  echo "Waiting for ClusterIssuer to be ready..."
  sleep 10
  
  echo "ClusterIssuer created successfully."
}

# Function to create Certificate
create_certificate() {
  local issuer_name="letsencrypt-$ENVIRONMENT"
  
  if [ "$STAGING" = true ]; then
    issuer_name="letsencrypt-staging"
  fi
  
  echo "Creating Certificate for $DOMAIN..."
  
  # Create Certificate manifest
  cat > /tmp/certificate.yaml << EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: $DOMAIN-tls
  namespace: $KUBERNETES_NAMESPACE
spec:
  secretName: $DOMAIN-tls
  issuerRef:
    name: $issuer_name
    kind: ClusterIssuer
  commonName: $DOMAIN
  dnsNames:
  - $DOMAIN
  - www.$DOMAIN
  - api.$DOMAIN
  duration: 2160h # 90 days
  renewBefore: 360h # 15 days
  privateKey:
    algorithm: ECDSA
    size: 256
EOF
  
  # Apply Certificate
  kubectl apply -f /tmp/certificate.yaml
  
  echo "Certificate created successfully."
  
  # Wait for Certificate to be ready
  echo "Waiting for Certificate to be issued..."
  kubectl wait --for=condition=Ready certificate/$DOMAIN-tls -n $KUBERNETES_NAMESPACE --timeout=300s
  
  echo "Certificate issued successfully."
}

# Function to create TLS Secret from existing certificate
create_tls_secret() {
  echo "Creating TLS Secret from existing certificate..."
  
  # Check if certificate files exist
  if [ ! -f "$CERTIFICATE_PATH" ]; then
    echo "Error: Certificate file not found at $CERTIFICATE_PATH"
    exit 1
  fi
  
  if [ ! -f "$PRIVATE_KEY_PATH" ]; then
    echo "Error: Private key file not found at $PRIVATE_KEY_PATH"
    exit 1
  fi
  
  # Create TLS Secret
  kubectl create secret tls "$DOMAIN-tls" \
    --namespace "$KUBERNETES_NAMESPACE" \
    --cert="$CERTIFICATE_PATH" \
    --key="$PRIVATE_KEY_PATH" \
    --dry-run=client -o yaml | kubectl apply -f -
  
  echo "TLS Secret created successfully."
}

# Function to update Ingress with TLS configuration
update_ingress() {
  echo "Updating Ingress with TLS configuration..."
  
  # Get current Ingress
  kubectl get ingress "$INGRESS_NAME" -n "$KUBERNETES_NAMESPACE" -o yaml > /tmp/ingress.yaml
  
  # Update Ingress with TLS configuration
  cat > /tmp/ingress-patch.yaml << EOF
spec:
  tls:
  - hosts:
    - $DOMAIN
    - www.$DOMAIN
    - api.$DOMAIN
    secretName: $DOMAIN-tls
  rules:
  - host: $DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: maily-web
            port:
              number: 80
  - host: www.$DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: maily-web
            port:
              number: 80
  - host: api.$DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: maily-api
            port:
              number: 80
EOF
  
  # Apply Ingress patch
  kubectl patch ingress "$INGRESS_NAME" -n "$KUBERNETES_NAMESPACE" --patch "$(cat /tmp/ingress-patch.yaml)"
  
  # Add annotations for TLS configuration
  kubectl annotate ingress "$INGRESS_NAME" -n "$KUBERNETES_NAMESPACE" \
    nginx.ingress.kubernetes.io/ssl-redirect=true \
    nginx.ingress.kubernetes.io/force-ssl-redirect=true \
    nginx.ingress.kubernetes.io/ssl-prefer-server-ciphers=true \
    nginx.ingress.kubernetes.io/ssl-ciphers="$CIPHERS" \
    nginx.ingress.kubernetes.io/ssl-protocols="TLSv$MIN_TLS_VERSION TLSv1.3" \
    --overwrite
  
  # Add HSTS annotations if enabled
  if [ "$HSTS_ENABLED" = true ]; then
    local hsts_header="max-age=$HSTS_MAX_AGE"
    
    if [ "$HSTS_INCLUDE_SUBDOMAINS" = true ]; then
      hsts_header="$hsts_header; includeSubDomains"
    fi
    
    if [ "$HSTS_PRELOAD" = true ]; then
      hsts_header="$hsts_header; preload"
    fi
    
    kubectl annotate ingress "$INGRESS_NAME" -n "$KUBERNETES_NAMESPACE" \
      nginx.ingress.kubernetes.io/hsts=true \
      nginx.ingress.kubernetes.io/hsts-max-age="$HSTS_MAX_AGE" \
      nginx.ingress.kubernetes.io/hsts-include-subdomains="$HSTS_INCLUDE_SUBDOMAINS" \
      nginx.ingress.kubernetes.io/hsts-preload="$HSTS_PRELOAD" \
      --overwrite
  fi
  
  # Add OCSP Stapling annotation if enabled
  if [ "$OCSP_STAPLING" = true ]; then
    kubectl annotate ingress "$INGRESS_NAME" -n "$KUBERNETES_NAMESPACE" \
      nginx.ingress.kubernetes.io/enable-ocsp-stapling=true \
      --overwrite
  fi
  
  echo "Ingress updated successfully."
}

# Function to configure Cloudflare SSL/TLS settings
configure_cloudflare() {
  echo "Configuring Cloudflare SSL/TLS settings..."
  
  if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "Error: Cloudflare API token not provided."
    exit 1
  fi
  
  # Get Cloudflare Zone ID
  ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')
  
  if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" = "null" ]; then
    echo "Error: Could not find Cloudflare zone for domain $DOMAIN"
    exit 1
  fi
  
  # Update SSL/TLS mode to Full (Strict)
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"value":"strict"}'
  
  # Enable HSTS
  if [ "$HSTS_ENABLED" = true ]; then
    curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_header" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" \
      --data "{\"value\":{\"strict_transport_security\":{\"enabled\":true,\"max_age\":$HSTS_MAX_AGE,\"include_subdomains\":$HSTS_INCLUDE_SUBDOMAINS,\"preload\":$HSTS_PRELOAD}}}"
  fi
  
  # Set minimum TLS version
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/min_tls_version" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{\"value\":\"$MIN_TLS_VERSION\"}"
  
  # Enable Automatic HTTPS Rewrites
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/automatic_https_rewrites" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"value":"on"}'
  
  # Enable Always Use HTTPS
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/always_use_https" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"value":"on"}'
  
  echo "Cloudflare SSL/TLS settings configured successfully."
}

# Main execution
echo "Configuring SSL/TLS for $DOMAIN in $ENVIRONMENT environment..."

# Install cert-manager if using Let's Encrypt
if [ "$USE_LETS_ENCRYPT" = true ]; then
  install_cert_manager
  create_cluster_issuer
  create_certificate
else
  create_tls_secret
fi

# Update Ingress with TLS configuration
update_ingress

# Configure Cloudflare if API token is provided
if [ -n "$CLOUDFLARE_API_TOKEN" ]; then
  configure_cloudflare
fi

echo "SSL/TLS configuration completed successfully."
echo
echo "Next steps:"
echo "1. Verify that the certificate is properly installed:"
echo "   kubectl get certificate -n $KUBERNETES_NAMESPACE"
echo "2. Test the HTTPS connection to your domain:"
echo "   curl -v https://$DOMAIN"
echo "3. Check the SSL/TLS configuration using SSL Labs:"
echo "   https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo "4. Set up automatic renewal monitoring"
echo "5. Implement Content Security Policy (CSP)"
echo "6. Consider implementing Certificate Transparency (CT) monitoring"
