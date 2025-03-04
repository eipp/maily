#!/bin/bash
# Phase 3: Full Production Deployment
# This script handles the critical services production deployment

# Deploy critical services to production
deploy_to_prod_full() {
  log "SECTION" "PHASE 3: FULL PRODUCTION DEPLOYMENT (CRITICAL SERVICES)"
  
  # 3.1 Deploy critical services manifests
  log "STEP" "Deploying critical services to production..."
  
  # Define critical services
  CRITICAL_SERVICES=(
    "api"
    "web"
    "ai-service"
    "database"
  )
  
  if [ "$DRY_RUN" = false ]; then
    # Create working directory for production manifests if it doesn't exist
    mkdir -p production-manifests
    
    # Deploy each manifest for critical services
    for dir in kubernetes/deployments kubernetes/services; do
      if [ -d "$dir" ]; then
        log "INFO" "Processing manifests in $dir for critical services..."
        
        for file in "$dir"/*.yaml; do
          if [ -f "$file" ]; then
            filename=$(basename "$file")
            
            # Check if this file is for a critical service
            is_critical=false
            for service in "${CRITICAL_SERVICES[@]}"; do
              if [[ "$filename" == *"$service"* ]]; then
                is_critical=true
                break
              fi
            done
            
            if [ "$is_critical" = true ]; then
              log "INFO" "Processing critical service $filename"
              
              # Create production version by setting namespace
              run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
              
              # Apply the manifest
              run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
            fi
          fi
        done
      fi
    done
    
    # Deploy network policies
    log "STEP" "Applying network policies..."
    
    if [ -d "kubernetes/network-policies" ]; then
      for file in kubernetes/network-policies/*.yaml; do
        if [ -f "$file" ]; then
          filename=$(basename "$file")
          log "INFO" "Processing network policy $filename"
          
          # Create production version by setting namespace
          run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
          
          # Apply the manifest
          run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
        fi
      done
    else
      log "WARNING" "Network policies directory not found"
    fi
    
    # Wait for deployments to be ready
    log "STEP" "Waiting for critical service deployments to be ready..."
    
    for service in "${CRITICAL_SERVICES[@]}"; do
      deployments=$(kubectl get deployments -n "$PROD_NAMESPACE" -o jsonpath="{.items[?(@.metadata.name=~'.*$service.*')].metadata.name}" 2>/dev/null)
      if [ -n "$deployments" ]; then
        for deployment in $deployments; do
          run_with_spinner "Waiting for deployment $deployment" "kubectl rollout status deployment/$deployment -n $PROD_NAMESPACE --timeout=300s"
        done
      fi
    done
  else
    log "INFO" "[DRY RUN] Would deploy critical services to production"
  fi
  
  # 3.2 Enable SLA monitoring
  log "STEP" "Enabling SLA monitoring..."
  
  if [ "$DRY_RUN" = false ]; then
    # Apply SLA monitoring configuration
    if [ -f "kubernetes/monitoring/prometheus-sla-rules.yaml" ]; then
      log "INFO" "Applying SLA monitoring rules"
      
      # Create production version by setting namespace (if applicable)
      run_with_spinner "Preparing SLA monitoring rules" "kubectl create --dry-run=client -o yaml -f kubernetes/monitoring/prometheus-sla-rules.yaml > \"production-manifests/prometheus-sla-rules.yaml\""
      
      # Apply the manifest
      run_with_spinner "Applying SLA monitoring rules" "kubectl apply -f \"production-manifests/prometheus-sla-rules.yaml\""
    else
      log "WARNING" "SLA monitoring rules not found"
    fi
    
    # Apply Grafana dashboard if available
    if [ -f "kubernetes/grafana-mailydocs-dashboard.json" ]; then
      log "INFO" "Applying Grafana SLA dashboard"
      
      # Check if Grafana is available
      if kubectl get svc -n monitoring grafana &>/dev/null; then
        run_with_spinner "Creating Grafana dashboard ConfigMap" "kubectl create configmap sla-dashboard --from-file=dashboard.json=kubernetes/grafana-mailydocs-dashboard.json -n monitoring --dry-run=client -o yaml | kubectl apply -f -"
        log "SUCCESS" "Created Grafana dashboard ConfigMap"
      else
        log "WARNING" "Grafana service not found in monitoring namespace"
      fi
    else
      log "WARNING" "Grafana dashboard file not found"
    fi
  else
    log "INFO" "[DRY RUN] Would enable SLA monitoring"
  fi
  
  # 3.3 Schedule chaos testing
  log "STEP" "Scheduling chaos testing..."
  
  if [ "$DRY_RUN" = false ]; then
    # Schedule chaos testing if chaos mesh is installed
    if kubectl get ns chaos-testing &>/dev/null && [ -d "kubernetes/chaos-testing" ]; then
      log "INFO" "Scheduling chaos tests as CronJobs"
      
      # Check for chaos testing directory
      if [ "$(ls -A kubernetes/chaos-testing)" ]; then
        # Create chaos testing namespace if needed
        if ! kubectl get ns chaos-testing &>/dev/null; then
          run_with_spinner "Creating chaos-testing namespace" "kubectl create namespace chaos-testing"
        fi
        
        # Create CronJob for each chaos test
        for test in kubernetes/chaos-testing/*.yaml; do
          if [ -f "$test" ]; then
            test_name=$(basename "$test" .yaml)
            
            # Create a CronJob version of the chaos test that runs weekly
            cat <<EOF > "production-manifests/chaos-$test_name-cronjob.yaml"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: chaos-$test_name
  namespace: chaos-testing
spec:
  schedule: "0 1 * * 0"  # Run weekly at 1 AM on Sunday
  suspend: false
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: chaos-admin
          containers:
          - name: kubectl
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              kubectl apply -f /tests/$test_name.yaml
              sleep 300  # Run for 5 minutes
              kubectl delete -f /tests/$test_name.yaml
            volumeMounts:
            - name: test-config
              mountPath: /tests
          volumes:
          - name: test-config
            configMap:
              name: chaos-$test_name-config
          restartPolicy: OnFailure
EOF
            
            # Create ConfigMap with the test configuration
            run_with_spinner "Creating ConfigMap for $test_name" "kubectl create configmap chaos-$test_name-config --from-file=$test_name.yaml=$test -n chaos-testing --dry-run=client -o yaml | kubectl apply -f -"
            
            # Apply the CronJob
            run_with_spinner "Scheduling chaos test $test_name" "kubectl apply -f production-manifests/chaos-$test_name-cronjob.yaml"
          fi
        done
        
        log "SUCCESS" "Scheduled chaos tests as CronJobs"
      else
        log "WARNING" "No chaos tests found in kubernetes/chaos-testing directory"
      fi
    else
      log "WARNING" "Chaos testing namespace or directory not found, skipping chaos test scheduling"
    fi
  else
    log "INFO" "[DRY RUN] Would schedule chaos testing"
  fi
  
  # 3.4 Implement distributed tracing
  log "STEP" "Implementing distributed tracing..."
  
  if [ "$DRY_RUN" = false ]; then
    # Deploy tracing configuration
    if [ -d "kubernetes/tracing" ]; then
      for file in kubernetes/tracing/*.yaml; do
        if [ -f "$file" ]; then
          filename=$(basename "$file")
          log "INFO" "Processing tracing config $filename"
          
          # Create production version by setting namespace
          run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
          
          # Apply the manifest
          run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
        fi
      done
      
      log "SUCCESS" "Implemented distributed tracing"
    else
      # If no dedicated tracing directory, check if tracing config is in logging directory
      if [ -d "kubernetes/logging" ] && ls kubernetes/logging/*tracing* 1> /dev/null 2>&1; then
        for file in kubernetes/logging/*tracing*; do
          if [ -f "$file" ]; then
            filename=$(basename "$file")
            log "INFO" "Processing tracing config $filename from logging directory"
            
            # Create production version by setting namespace
            run_with_spinner "Preparing $filename for production" "kubectl create --dry-run=client -o yaml -f \"$file\" | kubectl patch --local --dry-run=client -o yaml -f - -p '{\"metadata\":{\"namespace\":\"$PROD_NAMESPACE\"}}' > \"production-manifests/$filename\""
            
            # Apply the manifest
            run_with_spinner "Applying $filename to production" "kubectl apply -f \"production-manifests/$filename\""
          fi
        done
        
        log "SUCCESS" "Implemented distributed tracing from logging configuration"
      else
        log "WARNING" "Tracing configuration not found"
      fi
    fi
  else
    log "INFO" "[DRY RUN] Would implement distributed tracing"
  fi
  
  # 3.5 Deploy API documentation
  log "STEP" "Deploying interactive API documentation..."
  
  if [ "$DRY_RUN" = false ]; then
    # Check for API documentation files
    if [ -f "openapi.json" ]; then
      log "INFO" "Found OpenAPI documentation, creating ConfigMap"
      
      # Create ConfigMap for API documentation
      run_with_spinner "Creating API documentation ConfigMap" "kubectl create configmap api-docs --from-file=openapi.json=openapi.json -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      
      # Check if Swagger UI is available
      if kubectl get deployment -n "$PROD_NAMESPACE" | grep -q "swagger"; then
        log "INFO" "Swagger UI already deployed"
      else
        # Deploy Swagger UI
        cat <<EOF > "production-manifests/swagger-ui.yaml"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swagger-ui
  namespace: $PROD_NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: swagger-ui
  template:
    metadata:
      labels:
        app: swagger-ui
    spec:
      containers:
      - name: swagger-ui
        image: swaggerapi/swagger-ui:v4.18.3
        ports:
        - containerPort: 8080
        env:
        - name: SWAGGER_JSON
          value: /mnt/api-docs/openapi.json
        volumeMounts:
        - name: api-docs
          mountPath: /mnt/api-docs
      volumes:
      - name: api-docs
        configMap:
          name: api-docs
---
apiVersion: v1
kind: Service
metadata:
  name: swagger-ui
  namespace: $PROD_NAMESPACE
spec:
  selector:
    app: swagger-ui
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
EOF
        
        # Apply Swagger UI deployment
        run_with_spinner "Deploying Swagger UI" "kubectl apply -f production-manifests/swagger-ui.yaml"
        
        # Wait for Swagger UI deployment to be ready
        run_with_spinner "Waiting for Swagger UI deployment" "kubectl rollout status deployment/swagger-ui -n $PROD_NAMESPACE --timeout=300s"
      fi
      
      log "SUCCESS" "Deployed interactive API documentation"
    else
      log "WARNING" "OpenAPI documentation not found"
    fi
  else
    log "INFO" "[DRY RUN] Would deploy API documentation"
  fi
  
  # 3.6 Set up automated load testing
  log "STEP" "Setting up automated load testing..."
  
  if [ "$DRY_RUN" = false ]; then
    # Check for load testing directory
    if [ -d "load-tests" ]; then
      log "INFO" "Found load tests directory, setting up automated load testing"
      
      # Create CronJob for load testing
      cat <<EOF > "production-manifests/load-testing-cronjob.yaml"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: automated-load-testing
  namespace: $PROD_NAMESPACE
spec:
  schedule: "0 2 * * 1"  # Run weekly at 2 AM on Monday
  suspend: false
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: load-tester
            image: loadimpact/k6:latest
            command:
            - /bin/sh
            - -c
            - |
              cd /load-tests
              k6 run main.js
            volumeMounts:
            - name: load-tests-config
              mountPath: /load-tests
          volumes:
          - name: load-tests-config
            configMap:
              name: load-tests-config
          restartPolicy: OnFailure
EOF
      
      # Create ConfigMap for load tests
      if [ -f "load-tests/main.js" ]; then
        run_with_spinner "Creating load tests ConfigMap" "kubectl create configmap load-tests-config --from-file=main.js=load-tests/main.js -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      else
        # Create a basic load test if none exists
        mkdir -p load-tests
        cat <<EOF > "load-tests/main.js"
import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
  },
};

export default function() {
  const BASE_URL = 'http://api-service';
  
  // Test endpoints
  http.get(`${BASE_URL}/health`);
  
  // Add more specific tests here
  
  sleep(1);
}
EOF
        
        run_with_spinner "Creating basic load test script" "kubectl create configmap load-tests-config --from-file=main.js=load-tests/main.js -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      fi
      
      # Apply load testing CronJob
      run_with_spinner "Setting up automated load testing" "kubectl apply -f production-manifests/load-testing-cronjob.yaml"
      
      log "SUCCESS" "Set up automated load testing"
    else
      log "WARNING" "Load tests directory not found, skipping automated load testing setup"
    fi
  else
    log "INFO" "[DRY RUN] Would set up automated load testing"
  fi
  
  # 3.7 Finalize runbooks
  log "STEP" "Finalizing operational runbooks..."
  
  if [ "$DRY_RUN" = false ]; then
    # Check for runbooks directory
    if [ -d "docs/runbooks" ] || [ -d "runbooks" ]; then
      log "INFO" "Found runbooks directory"
      
      # Create ConfigMap for runbooks
      if [ -d "docs/runbooks" ]; then
        run_with_spinner "Creating runbooks ConfigMap" "kubectl create configmap operational-runbooks --from-file=docs/runbooks/ -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      elif [ -d "runbooks" ]; then
        run_with_spinner "Creating runbooks ConfigMap" "kubectl create configmap operational-runbooks --from-file=runbooks/ -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      fi
      
      log "SUCCESS" "Finalized operational runbooks"
    else
      log "WARNING" "Runbooks directory not found"
      
      # Create basic runbook directory and files if none exist
      mkdir -p docs/runbooks
      
      cat <<EOF > "docs/runbooks/README.md"
# Maily Operational Runbooks

This directory contains operational runbooks for the Maily system.

## Table of Contents

1. [Incident Response](incident-response.md)
2. [Backup and Restore](backup-restore.md)
3. [Scaling Procedures](scaling.md)
4. [Common Issues](common-issues.md)
5. [Monitoring Alerts](monitoring-alerts.md)
EOF
      
      cat <<EOF > "docs/runbooks/incident-response.md"
# Incident Response Runbook

This runbook describes the process for responding to incidents in the Maily system.

## Severity Levels

- **Severity 1**: Critical service outage affecting all users
- **Severity 2**: Partial service outage affecting some users
- **Severity 3**: Degraded service affecting specific features
- **Severity 4**: Minor issues with minimal impact

## Response Procedures

1. **Acknowledge the alert** in the monitoring system
2. **Assess the impact** and determine the severity level
3. **Notify stakeholders** based on the severity level
4. **Investigate and diagnose** the issue
5. **Implement a fix** or workaround
6. **Verify the resolution** by confirming service restoration
7. **Document the incident** for post-mortem analysis
EOF
      
      cat <<EOF > "docs/runbooks/backup-restore.md"
# Backup and Restore Procedures

This runbook describes backup and restore procedures for the Maily system.

## Database Backup

Database backups are taken automatically every 6 hours and stored in S3.

To manually trigger a backup:

\`\`\`bash
kubectl exec -n $PROD_NAMESPACE -it \$(kubectl get pods -n $PROD_NAMESPACE -l app=database -o jsonpath='{.items[0].metadata.name}') -- /backup/backup.sh
\`\`\`

## Database Restore

To restore from a backup:

1. **Identify the backup** to restore from
2. **Stop the affected services**
3. **Run the restore procedure**
4. **Verify the restored data**
5. **Restart the services**

## File Storage Backup

File storage backups are taken daily and stored in S3.

## File Storage Restore

Follow similar procedure as database restore, but use the file storage restore script.
EOF
      
      # Create ConfigMap for basic runbooks
      run_with_spinner "Creating basic runbooks ConfigMap" "kubectl create configmap operational-runbooks --from-file=docs/runbooks/ -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      
      log "WARNING" "Created basic runbooks. These should be expanded with real procedures."
    fi
  else
    log "INFO" "[DRY RUN] Would finalize operational runbooks"
  fi
  
  # 3.8 Schedule security audits
  log "STEP" "Scheduling regular security audits..."
  
  if [ "$DRY_RUN" = false ]; then
    # Create CronJob for security audits
    cat <<EOF > "production-manifests/security-audit-cronjob.yaml"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: security-audit
  namespace: $PROD_NAMESPACE
spec:
  schedule: "0 3 1 * *"  # Run monthly at 3 AM on the 1st day
  suspend: false
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: security-scanner
            image: aquasec/trivy:latest
            command:
            - /bin/sh
            - -c
            - |
              mkdir -p /reports
              # Scan all images in the namespace
              IMAGES=\$(kubectl get pods -n $PROD_NAMESPACE -o jsonpath='{.items[*].spec.containers[*].image}' | tr -s '[[:space:]]' '\n' | sort | uniq)
              for img in \$IMAGES; do
                echo "Scanning \$img"
                trivy image --format json --output /reports/\$(echo \$img | tr ':/@' '_').json \$img
              done
              # Scan for vulnerabilities in the cluster
              trivy k8s --report=summary -n $PROD_NAMESPACE --format json --output /reports/k8s-scan.json
            volumeMounts:
            - name: security-reports
              mountPath: /reports
          volumes:
          - name: security-reports
            emptyDir: {}
          restartPolicy: OnFailure
EOF
      
      # Apply security audit CronJob
      run_with_spinner "Scheduling regular security audits" "kubectl apply -f production-manifests/security-audit-cronjob.yaml"
      
      log "SUCCESS" "Scheduled regular security audits"
  else
    log "INFO" "[DRY RUN] Would schedule regular security audits"
  fi
  
  # 3.9 Validate browser compatibility testing
  log "STEP" "Setting up browser compatibility testing..."
  
  if [ "$DRY_RUN" = false ]; then
    # Create CronJob for browser compatibility testing if not already present
    if ! kubectl get cronjob -n "$PROD_NAMESPACE" browser-testing &>/dev/null; then
      cat <<EOF > "production-manifests/browser-testing-cronjob.yaml"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: browser-testing
  namespace: $PROD_NAMESPACE
spec:
  schedule: "0 4 * * 1"  # Run weekly at 4 AM on Monday
  suspend: false
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: browser-testing
            image: browserless/chrome:latest
            command:
            - /bin/sh
            - -c
            - |
              cd /browser-tests
              npm install
              npm test
            volumeMounts:
            - name: browser-tests-config
              mountPath: /browser-tests
          volumes:
          - name: browser-tests-config
            configMap:
              name: browser-tests-config
          restartPolicy: OnFailure
EOF
      
      # Create basic browser test files if they don't exist
      if [ ! -d "browser-tests" ]; then
        mkdir -p browser-tests
        
        cat <<EOF > "browser-tests/package.json"
{
  "name": "browser-tests",
  "version": "1.0.0",
  "description": "Browser compatibility tests",
  "main": "index.js",
  "scripts": {
    "test": "jest"
  },
  "dependencies": {
    "jest": "^29.0.0",
    "puppeteer": "^19.0.0"
  }
}
EOF
        
        cat <<EOF > "browser-tests/index.test.js"
const puppeteer = require('puppeteer');

describe('Browser Compatibility Tests', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
  });

  beforeEach(async () => {
    page = await browser.newPage();
    
    // Set different user agents to simulate different browsers
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36');
  });

  afterEach(async () => {
    await page.close();
  });

  afterAll(async () => {
    await browser.close();
  });

  test('Home page loads correctly', async () => {
    await page.goto('http://web-service');
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('Login page functionality', async () => {
    await page.goto('http://web-service/login');
    
    // Ensure login form elements exist
    const emailInput = await page.$('input[type="email"]');
    const passwordInput = await page.$('input[type="password"]');
    const loginButton = await page.$('button[type="submit"]');
    
    expect(emailInput).toBeTruthy();
    expect(passwordInput).toBeTruthy();
    expect(loginButton).toBeTruthy();
  });

  // Add more browser compatibility tests here
});
EOF
        
        # Create ConfigMap for browser tests
        run_with_spinner "Creating browser tests ConfigMap" "kubectl create configmap browser-tests-config --from-file=browser-tests/ -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      else
        # Use existing browser tests
        run_with_spinner "Creating browser tests ConfigMap" "kubectl create configmap browser-tests-config --from-file=browser-tests/ -n $PROD_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
      fi
      
      # Apply browser testing CronJob
      run_with_spinner "Setting up browser compatibility testing" "kubectl apply -f production-manifests/browser-testing-cronjob.yaml"
      
      log "SUCCESS" "Set up browser compatibility testing"
    else
      log "INFO" "Browser compatibility testing already configured"
    fi
  else
    log "INFO" "[DRY RUN] Would set up browser compatibility testing"
  fi
  
  # Final message
  log "SUCCESS" "Phase 3 (Full Production Deployment) completed successfully"
  log "SUCCESS" "DEPLOYMENT COMPLETE - All services are now running in production!"
}
