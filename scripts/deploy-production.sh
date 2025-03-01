#!/bin/bash
# Maily Production Deployment Script
# This script automates the deployment of Maily components to production
# Usage: ./deploy-production.sh [--skip-tests] [--skip-verification]

set -e

# Parse command line arguments
SKIP_TESTS=false
SKIP_VERIFICATION=false

for arg in "$@"
do
    case $arg in
        --skip-tests)
        SKIP_TESTS=true
        shift
        ;;
        --skip-verification)
        SKIP_VERIFICATION=true
        shift
        ;;
        *)
        # Unknown option
        ;;
    esac
done

# Configuration
NAMESPACE="maily-production"
DEPLOYMENT_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="deployment-$DEPLOYMENT_TIMESTAMP.log"

# Start logging
echo "Starting Maily production deployment at $(date)" | tee -a $LOG_FILE
echo "--------------------------------------------" | tee -a $LOG_FILE

# Function to run tests
run_tests() {
  echo "Running pre-deployment tests..." | tee -a $LOG_FILE

  # Email service tests
  echo "Running email service tests..." | tee -a $LOG_FILE
  cd apps/email-service
  npm run test | tee -a ../../$LOG_FILE

  # Load tests (reduced scope for pre-deployment)
  echo "Running load tests with reduced scope..." | tee -a ../../$LOG_FILE
  NODE_ENV=test npm run test:load -- --emails=100 --batch-size=25 --concurrent=2 | tee -a ../../$LOG_FILE
  cd ../..

  # Accessibility tests
  echo "Running accessibility tests..." | tee -a $LOG_FILE
  cd apps/web
  npm run test:a11y | tee -a ../../$LOG_FILE
  cd ../..

  echo "All tests completed successfully" | tee -a $LOG_FILE
}

# Function to verify Kubernetes namespace configuration
verify_namespace() {
  echo "Verifying namespace configuration..." | tee -a $LOG_FILE

  # Check if namespace exists
  if kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
    echo "Namespace $NAMESPACE exists" | tee -a $LOG_FILE
  else
    echo "Creating namespace $NAMESPACE..." | tee -a $LOG_FILE
    kubectl apply -f kubernetes/namespaces/production.yaml | tee -a $LOG_FILE
  fi

  # Verify security labels
  SECURITY_SCAN=$(kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels.security-scan}')
  COMPLIANCE_AUDIT=$(kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels.compliance-audit}')

  if [ "$SECURITY_SCAN" != "required" ] || [ "$COMPLIANCE_AUDIT" != "required" ]; then
    echo "ERROR: Namespace $NAMESPACE does not have required security labels!" | tee -a $LOG_FILE
    exit 1
  fi

  echo "Namespace configuration verified" | tee -a $LOG_FILE
}

# Function to deploy Kubernetes resources
deploy_resources() {
  echo "Deploying Kubernetes resources..." | tee -a $LOG_FILE

  # Apply ConfigMaps and Secrets
  echo "Applying ConfigMaps and Secrets..." | tee -a $LOG_FILE
  kubectl apply -f kubernetes/configmaps/ -n $NAMESPACE | tee -a $LOG_FILE

  # Note: In a real environment, secrets would be managed by a secrets manager
  # and not applied directly from files

  # Deploy services
  echo "Deploying services..." | tee -a $LOG_FILE
  kubectl apply -f kubernetes/services/ -n $NAMESPACE | tee -a $LOG_FILE

  # Deploy API service
  echo "Deploying API service..." | tee -a $LOG_FILE
  kubectl apply -f kubernetes/deployments/api-service.yaml -n $NAMESPACE | tee -a $LOG_FILE
  kubectl rollout status deployment/api-service -n $NAMESPACE | tee -a $LOG_FILE

  # Deploy email processing service
  echo "Deploying email processing service..." | tee -a $LOG_FILE
  kubectl apply -f kubernetes/deployments/email-processing-service.yaml -n $NAMESPACE | tee -a $LOG_FILE
  kubectl rollout status deployment/email-processing-service -n $NAMESPACE | tee -a $LOG_FILE

  # Deploy web frontend
  echo "Deploying web frontend..." | tee -a $LOG_FILE
  kubectl apply -f kubernetes/deployments/web-frontend.yaml -n $NAMESPACE | tee -a $LOG_FILE
  kubectl rollout status deployment/web-frontend -n $NAMESPACE | tee -a $LOG_FILE

  # Deploy worker services
  echo "Deploying worker services..." | tee -a $LOG_FILE
  kubectl apply -f kubernetes/deployments/analytics-worker.yaml -n $NAMESPACE | tee -a $LOG_FILE
  kubectl apply -f kubernetes/deployments/email-tracking-worker.yaml -n $NAMESPACE | tee -a $LOG_FILE

  echo "All services deployed successfully" | tee -a $LOG_FILE
}

# Function to verify deployment
verify_deployment() {
  echo "Verifying deployment..." | tee -a $LOG_FILE

  # Check all pods are running
  PENDING_PODS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[?(@.status.phase=="Pending")].metadata.name}')
  if [ -n "$PENDING_PODS" ]; then
    echo "ERROR: Some pods are still pending: $PENDING_PODS" | tee -a $LOG_FILE
    exit 1
  fi

  # Check for pods in CrashLoopBackOff
  CRASHLOOP_PODS=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[?(@.status.containerStatuses[0].state.waiting.reason=="CrashLoopBackOff")].metadata.name}')
  if [ -n "$CRASHLOOP_PODS" ]; then
    echo "ERROR: Some pods are in CrashLoopBackOff: $CRASHLOOP_PODS" | tee -a $LOG_FILE
    exit 1
  fi

  # Verify health endpoints
  echo "Verifying service health endpoints..." | tee -a $LOG_FILE

  # Get API service URL
  API_URL=$(kubectl get svc api-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
  if [ -z "$API_URL" ]; then
    API_URL=$(kubectl get svc api-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  fi

  # Check API health endpoint
  if [ -n "$API_URL" ]; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$API_URL/health)
    if [ $HTTP_STATUS -ne 200 ]; then
      echo "ERROR: API health check failed with status $HTTP_STATUS" | tee -a $LOG_FILE
      exit 1
    fi
    echo "API health check passed" | tee -a $LOG_FILE
  else
    echo "WARNING: Unable to verify API health - no external IP/hostname found" | tee -a $LOG_FILE
  fi

  echo "Deployment verification completed successfully" | tee -a $LOG_FILE
}

# Function to update DNS
update_dns() {
  echo "Updating DNS records..." | tee -a $LOG_FILE

  # Get load balancer IP/hostname
  LB_HOSTNAME=$(kubectl get svc web-frontend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
  if [ -z "$LB_HOSTNAME" ]; then
    LB_HOSTNAME=$(kubectl get svc web-frontend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  fi

  if [ -n "$LB_HOSTNAME" ]; then
    echo "Load balancer endpoint: $LB_HOSTNAME" | tee -a $LOG_FILE
    echo "Please update DNS records manually to point to this endpoint" | tee -a $LOG_FILE
    # In a real environment, you would use AWS CLI, GCP CLI, or an API to update DNS records
    # Example for AWS:
    # aws route53 change-resource-record-sets --hosted-zone-id YOUR_ZONE_ID --change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"app.justmaily.com","Type":"CNAME","TTL":300,"ResourceRecords":[{"Value":"'$LB_HOSTNAME'"}]}}]}'
  else
    echo "WARNING: Unable to update DNS - no external IP/hostname found" | tee -a $LOG_FILE
  fi
}

# Function to send notification
send_notification() {
  echo "Sending deployment notification..." | tee -a $LOG_FILE

  # In a real environment, you would send slack messages, emails, etc.
  # For this example, we'll just log it
  echo "Deployment completed successfully at $(date)" | tee -a $LOG_FILE

  # Create summary of deployment
  SUMMARY="Maily Production Deployment Summary\n"
  SUMMARY+="Deployment timestamp: $DEPLOYMENT_TIMESTAMP\n"
  SUMMARY+="Deployments:\n"
  SUMMARY+=$(kubectl get deployments -n $NAMESPACE -o wide | tee -a $LOG_FILE)

  echo -e $SUMMARY | tee -a $LOG_FILE
}

# Main deployment flow
echo "Starting deployment process..." | tee -a $LOG_FILE

# Step 1: Run tests if not skipped
if [ "$SKIP_TESTS" = false ]; then
  run_tests
else
  echo "Skipping tests as requested" | tee -a $LOG_FILE
fi

# Step 2: Verify namespace configuration
verify_namespace

# Step 3: Deploy resources
deploy_resources

# Step 4: Verify deployment if not skipped
if [ "$SKIP_VERIFICATION" = false ]; then
  verify_deployment
else
  echo "Skipping verification as requested" | tee -a $LOG_FILE
fi

# Step 5: Update DNS records
update_dns

# Step 6: Send notification
send_notification

echo "Deployment completed successfully!" | tee -a $LOG_FILE
echo "Deployment log saved to $LOG_FILE"
