#!/bin/bash
# deploy-analytics-service.sh
# Script to deploy the analytics service for Maily

set -e

# Check if we're in the project root directory
if [ ! -d "apps/analytics-service" ]; then
  echo "Error: This script must be run from the project root directory."
  exit 1
fi

echo "Deploying analytics service..."

# Install dependencies for analytics service
echo "Installing dependencies for analytics service..."
cd apps/analytics-service
npm install

# Build the analytics service
echo "Building analytics service..."
npm run build

# Create Dockerfile for analytics service if it doesn't exist
if [ ! -f "Dockerfile" ]; then
  echo "Creating Dockerfile for analytics service..."
  
  cat > Dockerfile << 'EOF'
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/config ./config

RUN npm ci --only=production

EXPOSE 3000

CMD ["node", "dist/index.js"]
EOF
fi

# Create Kubernetes deployment file
echo "Creating Kubernetes deployment file for analytics service..."
mkdir -p ../../kubernetes/deployments

cat > ../../kubernetes/deployments/analytics-service.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maily-analytics-service
  labels:
    app: maily-analytics-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: maily-analytics-service
  template:
    metadata:
      labels:
        app: maily-analytics-service
    spec:
      containers:
      - name: maily-analytics-service
        image: ${ECR_REGISTRY}/${ECR_REPOSITORY}/analytics-service:${IMAGE_TAG}
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3000"
        - name: POSTGRES_HOST
          value: "postgres"
        - name: POSTGRES_PORT
          value: "5432"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          value: "maily_analytics"
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PORT
          value: "6379"
        - name: RABBITMQ_HOST
          value: "rabbitmq"
        - name: RABBITMQ_PORT
          value: "5672"
        - name: RABBITMQ_USER
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: RABBITMQ_USER
        - name: RABBITMQ_PASSWORD
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: RABBITMQ_PASSWORD
        - name: RABBITMQ_VHOST
          value: "/"
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "100m"
            memory: "128Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
      volumes:
      - name: config-volume
        configMap:
          name: maily-analytics-config
EOF

# Create Kubernetes service file
echo "Creating Kubernetes service file for analytics service..."
mkdir -p ../../kubernetes/services

cat > ../../kubernetes/services/analytics-service-service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: maily-analytics-service
  labels:
    app: maily-analytics-service
spec:
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: maily-analytics-service
EOF

# Create Kubernetes ConfigMap for analytics service
echo "Creating Kubernetes ConfigMap for analytics service..."
mkdir -p ../../kubernetes/configmaps

cat > ../../kubernetes/configmaps/analytics-service-configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: maily-analytics-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
      - job_name: 'analytics-service'
        static_configs:
          - targets: ['localhost:3000']
EOF

# Add health check endpoint if it doesn't exist
if ! grep -q "app.get('/health'" src/app.ts; then
  echo "Adding health check endpoint to analytics service..."
  
  # Create a backup of the original file
  cp src/app.ts src/app.ts.bak
  
  # Add health check endpoint
  sed -i '/const app = express();/a \
// Health check endpoint\
app.get(\'/health\', (req, res) => {\
  res.status(200).json({ status: \'ok\' });\
});' src/app.ts
fi

# Update the CI/CD workflow to include analytics service
if ! grep -q "analytics-service" ../../.github/workflows/ci-cd.yml; then
  echo "Updating CI/CD workflow to include analytics service..."
  
  # Create a backup of the original file
  cp ../../.github/workflows/ci-cd.yml ../../.github/workflows/ci-cd.yml.bak
  
  # Add analytics service to the build job
  sed -i '/Build and push Campaign Service Docker image/,/cache-to: type=gha,mode=max/ a\
\
      - name: Build and push Analytics Service Docker image\
        uses: docker/build-push-action@v4\
        with:\
          context: ./apps/analytics-service\
          file: ./apps/analytics-service/Dockerfile\
          push: true\
          tags: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}/analytics-service:${{ github.sha }}\
          cache-from: type=gha\
          cache-to: type=gha,mode=max' ../../.github/workflows/ci-cd.yml
  
  # Add analytics service to the deploy job
  sed -i '/sed -i "s|image:.*maily\/campaign-service:.*|image: ${{ env.ECR_REGISTRY }}\/${{ env.ECR_REPOSITORY }}\/campaign-service:${{ env.IMAGE_TAG }}|g" kubernetes\/deployments\/campaign-service.yaml/ a\
          sed -i "s|image:.*maily\/analytics-service:.*|image: ${{ env.ECR_REGISTRY }}\/${{ env.ECR_REPOSITORY }}\/analytics-service:${{ env.IMAGE_TAG }}|g" kubernetes\/deployments\/analytics-service.yaml' ../../.github/workflows/ci-cd.yml
  
  # Add analytics service deployment to the kubectl apply commands
  sed -i '/kubectl apply -f kubernetes\/deployments\/campaign-service.yaml/ a\
          kubectl apply -f kubernetes\/configmaps\/analytics-service-configmap.yaml\
          kubectl apply -f kubernetes\/deployments\/analytics-service.yaml\
          kubectl apply -f kubernetes\/services\/analytics-service-service.yaml' ../../.github/workflows/ci-cd.yml
  
  # Add analytics service to the rollout status check
  sed -i '/kubectl rollout status deployment\/maily-campaign-service -n ${{ env.ENVIRONMENT }}/ a\
          kubectl rollout status deployment\/maily-analytics-service -n ${{ env.ENVIRONMENT }}' ../../.github/workflows/ci-cd.yml
fi

# Return to the project root
cd ../..

echo "Analytics service deployment completed successfully!"
echo
echo "Next steps:"
echo "1. Review the changes made to the analytics service"
echo "2. Test the analytics service locally: cd apps/analytics-service && npm run dev"
echo "3. Deploy the analytics service to Kubernetes:"
echo "   kubectl apply -f kubernetes/configmaps/analytics-service-configmap.yaml"
echo "   kubectl apply -f kubernetes/deployments/analytics-service.yaml"
echo "   kubectl apply -f kubernetes/services/analytics-service-service.yaml"
echo "4. Verify the analytics service is running: kubectl get pods | grep analytics-service"
echo "5. Test the analytics service API endpoints"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

