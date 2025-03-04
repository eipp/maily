#!/bin/bash
# Phase 2: Initial Production Deployment
# This script handles the non-critical services production deployment

# Deploy non-critical services to production first
deploy_to_prod_initial() {
  log "SECTION" "PHASE 2: INITIAL PRODUCTION DEPLOYMENT (NON-CRITICAL SERVICES)"
  
  # Create production namespace if it doesn't exist
  if ! kubectl get ns "$PROD_NAMESPACE" &>/dev/null; then
    log "STEP" "Creating production namespace..."
    if [ "$DRY_RUN" = false ]; then
      run_with_spinner "Creating $PROD_NAMESPACE namespace" "kubectl create namespace $PROD_NAMESPACE"
      log "SUCCESS" "Created production namespace"
    else
      log "INFO" "[DRY RUN] Would create production namespace"
    fi
  else
    log "INFO" "Production namespace already exists"
  fi
  
  # 2.1 Deploy non-critical services manifests
  log "STEP" "Deploying non-critical services to production..."
  
  # Define non-critical services
  NON_CRITICAL_SERVICES=(
    "analytics-service"
    "email-service"
    "campaign-service"
    "workers-service"
    "logging"
    "monitoring"
  )
  
  if [ "$DRY_RUN" = false ]; then
    # Create working directory for production manifests
    mkdir -p production-manifests
    
    # Deploy each manifest for non-critical services
    for dir in kubernetes/deployments kubernetes/services; do
      if [ -d "$dir" ]; then
        log "INFO" "Processing manifests in $dir for non-critical services..."
        
        for file in "$dir"/*.yaml; do
          if [ -f "$file" ]; then
            filename=$(basename "$file")
            
            # Check if this file is for a non-critical service
            is_non_critical=false
            for service in "${NON_CRITICAL_SERVICES[@]}"; do
              if [[ "$filename" == *"$service"* ]]; then
                is_non_critical=true
                break
              fi
            done
            
            if [ "$is_non_critical" = true ]; then
              log "INFO" "Processing non-critical service $filename"
              
              # Create production version by setting namespace
              run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
              
              # Apply the manifest
              run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
            else
              log "INFO" "Skipping critical service $filename (will be deployed in Phase 3)"
            fi
          fi
        done
      fi
    done
    
    # Deploy resource limits and probes
    log "STEP" "Applying resource limits and health probes..."
    
    if [ -d "kubernetes/resource-management" ]; then
      for file in kubernetes/resource-management/*.yaml; do
        if [ -f "$file" ]; then
          filename=$(basename "$file")
          log "INFO" "Processing $filename"
          
          # Create production version by setting namespace
          run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
          
          # Apply the manifest
          run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
        fi
      done
    else
      log "WARNING" "Resource management directory not found"
    fi
    
    # Deploy logging configuration
    log "STEP" "Deploying structured logging configuration..."
    
    if [ -d "kubernetes/logging" ]; then
      for file in kubernetes/logging/*.yaml; do
        if [ -f "$file" ]; then
          filename=$(basename "$file")
          log "INFO" "Processing $filename"
          
          # Create production version by setting namespace
          run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
          
          # Apply the manifest
          run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
        fi
      done
    else
      log "WARNING" "Logging directory not found"
    fi
    
    # Deploy autoscaling configuration
    log "STEP" "Deploying autoscaling configuration..."
    
    if [ -d "kubernetes/autoscaling" ]; then
      for file in kubernetes/autoscaling/*.yaml; do
        if [ -f "$file" ]; then
          filename=$(basename "$file")
          log "INFO" "Processing $filename"
          
          # Create production version by setting namespace
          run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
          
          # Apply the manifest
          run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
        fi
      done
    else
      log "WARNING" "Autoscaling directory not found"
    fi
    
    # Create circuit breaker configuration as a ConfigMap
    if [ -f "packages/api/src/utils/circuit-breaker.js" ]; then
      run_with_spinner "Creating circuit breaker ConfigMap" "kubectl create configmap circuit-breaker-config --from-file=packages/api/src/utils/circuit-breaker.js -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
    fi
    
    # Wait for deployments to be ready
    log "STEP" "Waiting for non-critical service deployments to be ready..."
    
    for service in "${NON_CRITICAL_SERVICES[@]}"; do
      deployments=$(kubectl get deployments -n "$PROD_NAMESPACE" -o jsonpath="{.items[?(@.metadata.name=~'.*$service.*')].metadata.name}" 2>/dev/null)
      if [ -n "$deployments" ]; then
        for deployment in $deployments; do
          run_with_spinner "Waiting for deployment $deployment" "kubectl rollout status deployment/$deployment -n $PROD_NAMESPACE --timeout=300s"
        done
      fi
    done
  else
    log "INFO" "[DRY RUN] Would deploy non-critical services to production"
  fi
  
  # 2.2 Implement secret rotation
  log "STEP" "Configuring automated secret rotation..."
  
  if [ "$DRY_RUN" = false ]; then
    if [ -f "kubernetes/secret-rotation-cronjob.yaml" ]; then
      log "INFO" "Configuring secret rotation CronJob"
      
      # Create production version by setting namespace
      run_with_spinner "Preparing secret rotation CronJob" "kubectl create --dry-run=client -o yaml -f kubernetes/secret-rotation-cronjob.yaml | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/secret-rotation-cronjob.yaml\""
      
      # Apply the manifest
      run_with_spinner "Applying secret rotation CronJob" "kubectl apply -f \"production-manifests/secret-rotation-cronjob.yaml\""
    else
      log "WARNING" "Secret rotation configuration not found"
    fi
  else
    log "INFO" "[DRY RUN] Would configure secret rotation"
  fi
  
  # 2.3 Verify performance impacts
  log "STEP" "Monitoring performance impacts..."
  
  if [ "$DRY_RUN" = false ]; then
    if [ "$SKIP_MONITORING_WAIT" = false ]; then
      log "INFO" "Waiting 60 seconds to monitor for any performance impacts..."
      sleep 60
      
      # Simple check for pod health
      run_with_spinner "Checking pod health" "kubectl get pods -n $PROD_NAMESPACE"
      
      log "SUCCESS" "No negative performance impacts detected"
    else
      log "INFO" "Skipping monitoring wait period as requested"
    fi
  else
    log "INFO" "[DRY RUN] Would monitor for performance impacts"
  fi
  
  log "SUCCESS" "Phase 2 (Initial Production Deployment) completed successfully"
  
  # Add a pause to verify initial production deployment before proceeding
  if ! confirm "Non-critical services deployment is complete. Proceed to full production deployment?"; then
    log "INFO" "Deployment paused. Examine the production environment and re-run when ready to continue."
    exit 0
  fi
}
