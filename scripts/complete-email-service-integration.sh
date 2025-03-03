#!/bin/bash
# complete-email-service-integration.sh
# Script to complete the email service integration for Maily

set -e

# Check if we're in the project root directory
if [ ! -d "apps/email-service" ]; then
  echo "Error: This script must be run from the project root directory."
  exit 1
fi

echo "Completing email service integration..."

# Install dependencies for email service
echo "Installing dependencies for email service..."
cd apps/email-service
npm install

# Build the email service
echo "Building email service..."
npm run build

# Create Kubernetes deployment files if they don't exist
if [ ! -f "kubernetes/deployments/email-service.yaml" ]; then
  echo "Creating Kubernetes deployment file for email service..."
  mkdir -p ../../kubernetes/deployments
  
  cat > ../../kubernetes/deployments/email-service.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maily-email-service
  labels:
    app: maily-email-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: maily-email-service
  template:
    metadata:
      labels:
        app: maily-email-service
    spec:
      containers:
      - name: maily-email-service
        image: ${ECR_REGISTRY}/${ECR_REPOSITORY}/email-service:${IMAGE_TAG}
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: EMAIL_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: maily-config
              key: EMAIL_PROVIDER
        - name: SENDGRID_API_KEY
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: SENDGRID_API_KEY
        - name: MAILGUN_API_KEY
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: MAILGUN_API_KEY
        - name: MAILGUN_DOMAIN
          valueFrom:
            configMapKeyRef:
              name: maily-config
              key: MAILGUN_DOMAIN
        - name: RESEND_API_KEY
          valueFrom:
            secretKeyRef:
              name: maily-secrets
              key: RESEND_API_KEY
        - name: EMAIL_FROM
          valueFrom:
            configMapKeyRef:
              name: maily-config
              key: EMAIL_FROM
        - name: EMAIL_FROM_NAME
          valueFrom:
            configMapKeyRef:
              name: maily-config
              key: EMAIL_FROM_NAME
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PORT
          value: "6379"
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
EOF
fi

# Create Kubernetes service file if it doesn't exist
if [ ! -f "../../kubernetes/services/email-service-service.yaml" ]; then
  echo "Creating Kubernetes service file for email service..."
  mkdir -p ../../kubernetes/services
  
  cat > ../../kubernetes/services/email-service-service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: maily-email-service
  labels:
    app: maily-email-service
spec:
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: maily-email-service
EOF
fi

# Create Dockerfile for email service if it doesn't exist
if [ ! -f "Dockerfile" ]; then
  echo "Creating Dockerfile for email service..."
  
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

RUN npm ci --only=production

EXPOSE 3000

CMD ["node", "dist/index.js"]
EOF
fi

# Create health check endpoint if it doesn't exist
if ! grep -q "app.get('/health'" src/index.ts; then
  echo "Adding health check endpoint to email service..."
  
  # Create a backup of the original file
  cp src/index.ts src/index.ts.bak
  
  # Add health check endpoint
  sed -i '/const app = express();/a \
// Health check endpoint\
app.get(\'/health\', (req, res) => {\
  res.status(200).json({ status: \'ok\' });\
});' src/index.ts
fi

# Update the CI/CD workflow to include email service
if ! grep -q "email-service" ../../.github/workflows/ci-cd.yml; then
  echo "Updating CI/CD workflow to include email service..."
  
  # Create a backup of the original file
  cp ../../.github/workflows/ci-cd.yml ../../.github/workflows/ci-cd.yml.bak
  
  # Add email service to the build job
  sed -i '/Build and push Web Docker image/,/cache-to: type=gha,mode=max/ a\
\
      - name: Build and push Email Service Docker image\
        uses: docker/build-push-action@v4\
        with:\
          context: ./apps/email-service\
          file: ./apps/email-service/Dockerfile\
          push: true\
          tags: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}/email-service:${{ github.sha }}\
          cache-from: type=gha\
          cache-to: type=gha,mode=max' ../../.github/workflows/ci-cd.yml
  
  # Add email service to the deploy job
  sed -i '/sed -i "s|image:.*maily\/web:.*|image: ${{ env.ECR_REGISTRY }}\/${{ env.ECR_REPOSITORY }}\/web:${{ env.IMAGE_TAG }}|g" kubernetes\/deployments\/maily-unified.yaml/ a\
          sed -i "s|image:.*maily\/email-service:.*|image: ${{ env.ECR_REGISTRY }}\/${{ env.ECR_REPOSITORY }}\/email-service:${{ env.IMAGE_TAG }}|g" kubernetes\/deployments\/email-service.yaml' ../../.github/workflows/ci-cd.yml
  
  # Add email service deployment to the kubectl apply commands
  sed -i '/kubectl apply -f kubernetes\/deployments\/maily-unified.yaml/ a\
          kubectl apply -f kubernetes\/deployments\/email-service.yaml\
          kubectl apply -f kubernetes\/services\/email-service-service.yaml' ../../.github/workflows/ci-cd.yml
  
  # Add email service to the rollout status check
  sed -i '/kubectl rollout status deployment\/maily-web -n ${{ env.ENVIRONMENT }}/ a\
          kubectl rollout status deployment\/maily-email-service -n ${{ env.ENVIRONMENT }}' ../../.github/workflows/ci-cd.yml
fi

# Return to the project root
cd ../..

echo "Email service integration completed successfully!"
echo
echo "Next steps:"
echo "1. Review the changes made to the email service"
echo "2. Test the email service locally: cd apps/email-service && npm run dev"
echo "3. Deploy the email service to Kubernetes: kubectl apply -f kubernetes/deployments/email-service.yaml -f kubernetes/services/email-service-service.yaml"
echo "4. Verify the email service is running: kubectl get pods | grep email-service"
echo "5. Test sending an email through the service"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

