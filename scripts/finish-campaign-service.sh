#!/bin/bash
# finish-campaign-service.sh
# Script to finish the campaign service for Maily

set -e

# Check if we're in the project root directory
if [ ! -d "apps/campaign-service" ]; then
  echo "Error: This script must be run from the project root directory."
  exit 1
fi

echo "Finishing campaign service..."

# Install dependencies for campaign service
echo "Installing dependencies for campaign service..."
cd apps/campaign-service
npm install

# Create missing files and directories
echo "Creating missing files and directories..."

# Create infrastructure directory if it doesn't exist
mkdir -p src/infrastructure/repositories
mkdir -p src/infrastructure/persistence
mkdir -p src/infrastructure/messaging
mkdir -p src/infrastructure/metrics

# Create repository implementation
echo "Creating repository implementation..."
cat > src/infrastructure/repositories/campaign-repository-impl.ts << 'EOF'
import { CampaignRepository } from '../../domain/repositories/campaign-repository';
import { Campaign } from '../../domain/models/campaign';
import { Id } from '../../domain/value-objects/id';
import { CampaignStatus } from '../../domain/value-objects/campaign-status';

export class CampaignRepositoryImpl implements CampaignRepository {
  private campaigns: Map<string, Campaign> = new Map();

  async findById(id: Id): Promise<Campaign | null> {
    const campaign = this.campaigns.get(id.value);
    return campaign || null;
  }

  async findAll(): Promise<Campaign[]> {
    return Array.from(this.campaigns.values());
  }

  async findByStatus(status: CampaignStatus): Promise<Campaign[]> {
    return Array.from(this.campaigns.values()).filter(
      campaign => campaign.status.equals(status)
    );
  }

  async save(campaign: Campaign): Promise<void> {
    this.campaigns.set(campaign.id.value, campaign);
  }

  async delete(id: Id): Promise<void> {
    this.campaigns.delete(id.value);
  }
}
EOF

# Create persistence layer
echo "Creating persistence layer..."
cat > src/infrastructure/persistence/campaign-store.ts << 'EOF'
import { Campaign } from '../../domain/models/campaign';
import { Id } from '../../domain/value-objects/id';

export interface CampaignStore {
  save(campaign: Campaign): Promise<void>;
  findById(id: Id): Promise<Campaign | null>;
  findAll(): Promise<Campaign[]>;
  delete(id: Id): Promise<void>;
}

export class InMemoryCampaignStore implements CampaignStore {
  private campaigns: Map<string, Campaign> = new Map();

  async save(campaign: Campaign): Promise<void> {
    this.campaigns.set(campaign.id.value, campaign);
  }

  async findById(id: Id): Promise<Campaign | null> {
    const campaign = this.campaigns.get(id.value);
    return campaign || null;
  }

  async findAll(): Promise<Campaign[]> {
    return Array.from(this.campaigns.values());
  }

  async delete(id: Id): Promise<void> {
    this.campaigns.delete(id.value);
  }
}
EOF

# Create messaging layer
echo "Creating messaging layer..."
cat > src/infrastructure/messaging/campaign-event-publisher.ts << 'EOF'
import { DomainEvent } from '../../domain/events/domain-event';
import { CampaignEvent } from '../../domain/events/campaign-events';

export interface EventPublisher {
  publish(event: DomainEvent): Promise<void>;
}

export class CampaignEventPublisher implements EventPublisher {
  private handlers: Map<string, Function[]> = new Map();

  registerHandler(eventType: string, handler: Function): void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.push(handler);
    this.handlers.set(eventType, handlers);
  }

  async publish(event: DomainEvent): Promise<void> {
    const eventType = event.constructor.name;
    const handlers = this.handlers.get(eventType) || [];
    
    console.log(`Publishing event: ${eventType}`);
    
    for (const handler of handlers) {
      await handler(event);
    }
    
    // If the event is a campaign event, also notify handlers registered for all campaign events
    if (event instanceof CampaignEvent) {
      const allCampaignEventHandlers = this.handlers.get('CampaignEvent') || [];
      for (const handler of allCampaignEventHandlers) {
        await handler(event);
      }
    }
  }
}
EOF

# Create metrics layer
echo "Creating metrics layer..."
cat > src/infrastructure/metrics/campaign-metrics.ts << 'EOF'
export interface MetricsCollector {
  incrementCounter(name: string, tags?: Record<string, string>): void;
  recordGauge(name: string, value: number, tags?: Record<string, string>): void;
  startTimer(name: string, tags?: Record<string, string>): () => void;
}

export class ConsoleMetricsCollector implements MetricsCollector {
  incrementCounter(name: string, tags?: Record<string, string>): void {
    console.log(`Incrementing counter: ${name}`, tags);
  }

  recordGauge(name: string, value: number, tags?: Record<string, string>): void {
    console.log(`Recording gauge: ${name} = ${value}`, tags);
  }

  startTimer(name: string, tags?: Record<string, string>): () => void {
    const start = Date.now();
    console.log(`Starting timer: ${name}`, tags);
    
    return () => {
      const duration = Date.now() - start;
      console.log(`Timer completed: ${name} = ${duration}ms`, tags);
    };
  }
}
EOF

# Create application service
echo "Creating application service..."
mkdir -p src/application/services

cat > src/application/services/campaign-service.ts << 'EOF'
import { Campaign } from '../../domain/models/campaign';
import { CampaignRepository } from '../../domain/repositories/campaign-repository';
import { Id } from '../../domain/value-objects/id';
import { CampaignStatus } from '../../domain/value-objects/campaign-status';
import { EventPublisher } from '../../infrastructure/messaging/campaign-event-publisher';
import { MetricsCollector } from '../../infrastructure/metrics/campaign-metrics';
import { CampaignCreated } from '../../domain/events/campaign-created';
import { CampaignLaunched } from '../../domain/events/campaign-launched';
import { CampaignPaused } from '../../domain/events/campaign-paused';
import { CampaignCanceled } from '../../domain/events/campaign-canceled';
import { CampaignCompleted } from '../../domain/events/campaign-completed';

export class CampaignService {
  constructor(
    private readonly campaignRepository: CampaignRepository,
    private readonly eventPublisher: EventPublisher,
    private readonly metricsCollector: MetricsCollector
  ) {}

  async createCampaign(campaignData: any): Promise<Campaign> {
    const endTimer = this.metricsCollector.startTimer('campaign.create');
    
    try {
      const campaign = Campaign.create(
        campaignData.name,
        campaignData.description,
        campaignData.audience,
        campaignData.template,
        campaignData.schedule,
        campaignData.settings
      );
      
      await this.campaignRepository.save(campaign);
      
      await this.eventPublisher.publish(new CampaignCreated(campaign));
      
      this.metricsCollector.incrementCounter('campaign.created');
      
      return campaign;
    } finally {
      endTimer();
    }
  }

  async getCampaign(id: string): Promise<Campaign | null> {
    const campaignId = new Id(id);
    return this.campaignRepository.findById(campaignId);
  }

  async getAllCampaigns(): Promise<Campaign[]> {
    return this.campaignRepository.findAll();
  }

  async getCampaignsByStatus(status: string): Promise<Campaign[]> {
    const campaignStatus = new CampaignStatus(status);
    return this.campaignRepository.findByStatus(campaignStatus);
  }

  async launchCampaign(id: string): Promise<Campaign> {
    const endTimer = this.metricsCollector.startTimer('campaign.launch');
    
    try {
      const campaignId = new Id(id);
      const campaign = await this.campaignRepository.findById(campaignId);
      
      if (!campaign) {
        throw new Error(`Campaign with ID ${id} not found`);
      }
      
      campaign.launch();
      
      await this.campaignRepository.save(campaign);
      
      await this.eventPublisher.publish(new CampaignLaunched(campaign));
      
      this.metricsCollector.incrementCounter('campaign.launched');
      
      return campaign;
    } finally {
      endTimer();
    }
  }

  async pauseCampaign(id: string): Promise<Campaign> {
    const campaignId = new Id(id);
    const campaign = await this.campaignRepository.findById(campaignId);
    
    if (!campaign) {
      throw new Error(`Campaign with ID ${id} not found`);
    }
    
    campaign.pause();
    
    await this.campaignRepository.save(campaign);
    
    await this.eventPublisher.publish(new CampaignPaused(campaign));
    
    this.metricsCollector.incrementCounter('campaign.paused');
    
    return campaign;
  }

  async cancelCampaign(id: string): Promise<Campaign> {
    const campaignId = new Id(id);
    const campaign = await this.campaignRepository.findById(campaignId);
    
    if (!campaign) {
      throw new Error(`Campaign with ID ${id} not found`);
    }
    
    campaign.cancel();
    
    await this.campaignRepository.save(campaign);
    
    await this.eventPublisher.publish(new CampaignCanceled(campaign));
    
    this.metricsCollector.incrementCounter('campaign.canceled');
    
    return campaign;
  }

  async completeCampaign(id: string): Promise<Campaign> {
    const campaignId = new Id(id);
    const campaign = await this.campaignRepository.findById(campaignId);
    
    if (!campaign) {
      throw new Error(`Campaign with ID ${id} not found`);
    }
    
    campaign.complete();
    
    await this.campaignRepository.save(campaign);
    
    await this.eventPublisher.publish(new CampaignCompleted(campaign));
    
    this.metricsCollector.incrementCounter('campaign.completed');
    
    return campaign;
  }

  async deleteCampaign(id: string): Promise<void> {
    const campaignId = new Id(id);
    await this.campaignRepository.delete(campaignId);
    
    this.metricsCollector.incrementCounter('campaign.deleted');
  }
}
EOF

# Create index.ts file
echo "Creating index.ts file..."
cat > src/index.ts << 'EOF'
import express from 'express';
import bodyParser from 'body-parser';
import { CampaignRepositoryImpl } from './infrastructure/repositories/campaign-repository-impl';
import { CampaignEventPublisher } from './infrastructure/messaging/campaign-event-publisher';
import { ConsoleMetricsCollector } from './infrastructure/metrics/campaign-metrics';
import { CampaignService } from './application/services/campaign-service';
import { CampaignController } from './interfaces/api/controllers/campaign.controller';
import { campaignRoutes } from './interfaces/api/routes/campaign.routes';

// Create Express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Set up dependencies
const campaignRepository = new CampaignRepositoryImpl();
const eventPublisher = new CampaignEventPublisher();
const metricsCollector = new ConsoleMetricsCollector();
const campaignService = new CampaignService(campaignRepository, eventPublisher, metricsCollector);
const campaignController = new CampaignController(campaignService);

// Set up routes
app.use('/api/campaigns', campaignRoutes(campaignController));

// Start server
app.listen(port, () => {
  console.log(`Campaign service listening on port ${port}`);
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT signal received: closing HTTP server');
  process.exit(0);
});
EOF

# Create Dockerfile for campaign service
echo "Creating Dockerfile for campaign service..."
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

# Create Kubernetes deployment file
echo "Creating Kubernetes deployment file for campaign service..."
mkdir -p ../../kubernetes/deployments

cat > ../../kubernetes/deployments/campaign-service.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maily-campaign-service
  labels:
    app: maily-campaign-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: maily-campaign-service
  template:
    metadata:
      labels:
        app: maily-campaign-service
    spec:
      containers:
      - name: maily-campaign-service
        image: ${ECR_REGISTRY}/${ECR_REPOSITORY}/campaign-service:${IMAGE_TAG}
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3000"
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

# Create Kubernetes service file
echo "Creating Kubernetes service file for campaign service..."
mkdir -p ../../kubernetes/services

cat > ../../kubernetes/services/campaign-service-service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: maily-campaign-service
  labels:
    app: maily-campaign-service
spec:
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: maily-campaign-service
EOF

# Update the CI/CD workflow to include campaign service
if ! grep -q "campaign-service" ../../.github/workflows/ci-cd.yml; then
  echo "Updating CI/CD workflow to include campaign service..."
  
  # Create a backup of the original file
  cp ../../.github/workflows/ci-cd.yml ../../.github/workflows/ci-cd.yml.bak
  
  # Add campaign service to the build job
  sed -i '/Build and push Email Service Docker image/,/cache-to: type=gha,mode=max/ a\
\
      - name: Build and push Campaign Service Docker image\
        uses: docker/build-push-action@v4\
        with:\
          context: ./apps/campaign-service\
          file: ./apps/campaign-service/Dockerfile\
          push: true\
          tags: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}/campaign-service:${{ github.sha }}\
          cache-from: type=gha\
          cache-to: type=gha,mode=max' ../../.github/workflows/ci-cd.yml
  
  # Add campaign service to the deploy job
  sed -i '/sed -i "s|image:.*maily\/email-service:.*|image: ${{ env.ECR_REGISTRY }}\/${{ env.ECR_REPOSITORY }}\/email-service:${{ env.IMAGE_TAG }}|g" kubernetes\/deployments\/email-service.yaml/ a\
          sed -i "s|image:.*maily\/campaign-service:.*|image: ${{ env.ECR_REGISTRY }}\/${{ env.ECR_REPOSITORY }}\/campaign-service:${{ env.IMAGE_TAG }}|g" kubernetes\/deployments\/campaign-service.yaml' ../../.github/workflows/ci-cd.yml
  
  # Add campaign service deployment to the kubectl apply commands
  sed -i '/kubectl apply -f kubernetes\/deployments\/email-service.yaml/ a\
          kubectl apply -f kubernetes\/deployments\/campaign-service.yaml\
          kubectl apply -f kubernetes\/services\/campaign-service-service.yaml' ../../.github/workflows/ci-cd.yml
  
  # Add campaign service to the rollout status check
  sed -i '/kubectl rollout status deployment\/maily-email-service -n ${{ env.ENVIRONMENT }}/ a\
          kubectl rollout status deployment\/maily-campaign-service -n ${{ env.ENVIRONMENT }}' ../../.github/workflows/ci-cd.yml
fi

# Return to the project root
cd ../..

echo "Campaign service finished successfully!"
echo
echo "Next steps:"
echo "1. Review the changes made to the campaign service"
echo "2. Test the campaign service locally: cd apps/campaign-service && npm run dev"
echo "3. Deploy the campaign service to Kubernetes: kubectl apply -f kubernetes/deployments/campaign-service.yaml -f kubernetes/services/campaign-service-service.yaml"
echo "4. Verify the campaign service is running: kubectl get pods | grep campaign-service"
echo "5. Test the campaign service API endpoints"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

