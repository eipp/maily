# Maily - AI-Powered Email Campaign Platform

Maily is a modern, AI-powered email campaign platform that combines real-time collaboration with interactive design capabilities. It features a robust backend powered by multiple AI providers and a responsive frontend built with Next.js.

## Features

### Backend
- Multi-provider AI integration (OpenAI, Anthropic, Google, etc.)
- Real-time collaboration using Socket.IO
- Distributed computing with Ray
- Redis caching for performance optimization
- PostgreSQL database for data persistence
- FastAPI for high-performance API endpoints
- Comprehensive error handling and logging
- Environment-based configuration
- CORS support for secure cross-origin requests

### Advanced AI Features
- **Orchestration**: Distributed task management using Ray for scalable AI workloads
- **RAG (Retrieval-Augmented Generation)**: Enhanced content generation with real-time data retrieval
- **Personalization**: Dynamic content tailoring using user data and Jinja2 templates
- **Delivery Optimization**: ML-powered optimal delivery time prediction

### Frontend
- Real-time chat interface
- Interactive canvas editor
- Redux state management
- Responsive design with Tailwind CSS
- TypeScript for type safety
- Socket.IO for real-time updates
- Fabric.js for canvas manipulation

## Project Structure

```
maily/
├── backend/           # FastAPI backend application
│   ├── main.py       # Main application entry point
│   ├── test_main.py  # Backend tests
│   └── requirements.txt  # Python dependencies
│
├── maily-frontend/   # Next.js frontend application
│   ├── app/         # Main source directory
│   │   ├── components/  # Reusable React components
│   │   ├── hooks/      # Custom React hooks
│   │   ├── utils/      # Utility functions
│   │   ├── workers/    # Web workers
│   │   └── __tests__/  # Frontend tests
│   ├── public/      # Static assets
│   └── package.json # Node.js dependencies
│
└── .gitignore      # Git ignore rules
```

## Directory Structure Overview

### Backend (`/backend`)
- Contains the FastAPI application
- Handles API endpoints, database operations, and business logic
- Includes tests and dependency management

### Frontend (`/maily-frontend`)
- Next.js application with TypeScript
- Modern React components and hooks
- Comprehensive test suite
- Tailwind CSS for styling

### Configuration
- Environment variables are managed through `.env` files (not tracked in git)
- Separate configurations for development and production environments

## Development Setup

### Prerequisites
- Node.js 18+
- Python 3.10+
- Virtual environment (recommended to be stored outside the project directory)

### Backend Setup
1. Create a virtual environment (recommended location: `~/venvs/maily-env-py310`)
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Copy `.env.example` to `.env` and configure

### Frontend Setup
1. Navigate to `maily-frontend`
2. Install dependencies: `npm install`
3. Copy `.env.example` to `.env.local` and configure
4. Run development server: `npm run dev`

## Testing
- Backend: Run `pytest` in the backend directory
- Frontend: Run `npm test` in the maily-frontend directory

## Contributing
Please follow the established directory structure when adding new features:
- Place frontend components in `maily-frontend/app/components`
- Add frontend tests in `maily-frontend/app/__tests__`
- Backend code goes in appropriate modules under `backend/`

## Directory Structure

The project is organized into the following key directories:

### Root Directory
- `backend/` - Backend application code
  - `main.py` - Backend application entry point
  - `requirements.txt` - Python dependencies
  - `tests/` - Backend test suites
- `maily-frontend/` - Next.js frontend application
  - `app/` - Next.js application code
    - `components/` - Reusable React components
    - `hooks/` - Custom React hooks
    - `utils/` - Utility functions and helpers
    - `workers/` - Web workers for background processing
    - `__tests__/` - Frontend test files
  - `public/` - Static assets
  - `.next/` - Next.js build output
  - `node_modules/` - Frontend dependencies

### Backend Directory (`src/`)
- Contains the backend application code
- Organized by feature and responsibility
- Includes AI providers integration, database models, and API endpoints

### Tests Directory (`tests/`)
- Unit tests, integration tests, and end-to-end tests for the backend
- Organized to mirror the src directory structure

## Prerequisites

- Node.js (v18 or higher)
- Python (v3.9 or higher)
- PostgreSQL
- Redis
- npm or yarn
- Pinecone account (for RAG feature)
- Docker (optional, for containerization)

## Installation

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd maily
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add the following (replace with your values):
```env
# Database Configuration
POSTGRES_USER=your_user
POSTGRES_DB=maily
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# API Configuration
API_KEY=your-secure-api-key-here

# AI Provider API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=your_pinecone_environment
# Add other provider keys as needed
```

5. Start the required services:
```bash
# Start Redis server
redis-server

# Start Celery worker (in a separate terminal)
celery -A delivery worker --loglevel=info

# Start the backend server
uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd maily-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
Create a `.env.local` file in the frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

## Frontend Development

The frontend is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

### Quick Start

1. Navigate to the frontend directory:
```bash
cd maily-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Advanced Features Usage

### Orchestration
The Ray-based orchestration system manages distributed tasks across multiple agents:
```python
# Example API call
POST /orchestrate
{
    "task_type": "content",
    "payload": "Generate email for product launch"
}
```

### RAG (Retrieval-Augmented Generation)
Enhances content generation by incorporating relevant knowledge base data:
```python
# Example API call
POST /generate-with-rag
{
    "query": "Latest trends in email marketing"
}
```

### Personalization
Dynamically tailors content based on user data and preferences:
```python
# Example API call
POST /personalize-email
{
    "user_id": 1,
    "template_id": "product_recommendation"
}
```

### Delivery Optimization
Uses ML to predict optimal delivery times:
```python
# Example API call
POST /schedule-email
{
    "user_id": 1,
    "email_content": "Your personalized content",
    "optimize_delivery": true
}
```

## Docker Deployment

Build and run the application using Docker:

```bash
# Build the image
docker build -t maily .

# Run the container
docker run -p 8000:8000 maily
```

## API Documentation

The backend API is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Key endpoints:
- POST `/create_campaign`: Create a new email campaign
- POST `/configure_model`: Configure AI model settings
- POST `/orchestrate`: Manage distributed tasks
- POST `/generate-with-rag`: Generate content with knowledge base integration
- POST `/personalize-email`: Create personalized email content
- POST `/schedule-email`: Schedule optimized email delivery

## Architecture

### Backend
- FastAPI for the REST API
- Socket.IO for real-time communication
- Ray for distributed computing
- Redis for caching
- PostgreSQL for data storage
- Multiple AI provider integrations
- Pinecone for vector search
- Celery for task scheduling
- scikit-learn for delivery optimization

### Frontend
- Next.js for the React framework
- Redux for state management
- Socket.IO client for real-time updates
- Fabric.js for canvas manipulation
- Tailwind CSS for styling

## Testing

### Backend Tests
```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run end-to-end tests
pytest tests/e2e

# Generate coverage report
pytest --cov=app tests/
```

### Frontend Tests
```bash
# Run unit tests
cd maily-frontend
npm test

# Run end-to-end tests
npm run test:e2e

# Run component tests
npm run test:component
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```
   Error: Error connecting to Redis on localhost:6379
   ```
   Solution: Ensure Redis server is running and accessible:
   ```bash
   redis-cli ping  # Should return PONG
   ```

2. **PostgreSQL Connection Issues**
   ```
   Error: Connection refused for database "maily"
   ```
   Solution: Verify PostgreSQL service and credentials:
   ```bash
   psql -U your_user -d maily  # Should connect to database
   ```

3. **Celery Worker Not Starting**
   ```
   Error: No nodes available
   ```
   Solution: Check Redis and restart Celery worker:
   ```bash
   celery -A delivery worker --loglevel=info
   ```

4. **Ray Cluster Issues**
   ```
   Error: Cannot connect to Ray cluster
   ```
   Solution: Restart Ray:
   ```bash
   ray stop
   ray start --head
   ```

### Debugging

1. Enable debug logging in `.env`:
   ```env
   LOG_LEVEL=DEBUG
   ```

2. Check application logs:
   ```bash
   tail -f logs/maily.log
   ```

3. Monitor Redis:
   ```bash
   redis-cli monitor
   ```

## Security

### Best Practices

1. **API Keys**
   - Never commit API keys to version control
   - Rotate keys regularly
   - Use environment variables for all sensitive data

2. **Authentication**
   - JWT tokens for API authentication
   - Rate limiting on all endpoints
   - CORS configuration for frontend security

3. **Data Protection**
   - Encryption at rest for sensitive data
   - Regular security audits
   - GDPR compliance measures

### Security Headers
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring

### Application Metrics

1. **Prometheus Integration**
   ```bash
   # Start Prometheus
   docker run -p 9090:9090 -v ./prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
   ```

2. **Grafana Dashboards**
   ```bash
   # Start Grafana
   docker run -p 3000:3000 grafana/grafana
   ```

### Key Metrics
- API endpoint latency
- Queue processing time
- Error rates
- Resource utilization
- AI model performance

### Health Checks
```bash
# Check application health
curl http://localhost:8000/health

# Check Redis health
redis-cli ping

# Check PostgreSQL health
pg_isready -h localhost -p 5432
```

## Performance Optimization

### Performance Benchmarks
- Backend API response time: < 200ms for 95% of requests
- Frontend initial load time: < 2s
- Chat message delivery: < 100ms
- Canvas rendering: < 50ms for updates

### Backend Optimizations

#### Model Optimization
```python
import onnxruntime as ort
import numpy as np

class OptimizedModelInference:
    def __init__(self, model_path):
        self.session = ort.InferenceSession(model_path)
        
    def predict(self, input_data):
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name
        result = self.session.run([output_name], {input_name: input_data})
        return result[0]
```

#### Redis Caching
```python
from fastapi import FastAPI, HTTPException
import redis
import json

app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/user/{user_id}")
async def get_user(user_id: int):
    cache_key = f"user:{user_id}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
        
    user_data = await fetch_from_db(user_id)
    redis_client.setex(cache_key, 3600, json.dumps(user_data))
    return user_data
```

#### Database Optimization
```sql
-- Optimize frequently used queries
CREATE INDEX idx_user_id ON campaigns (user_id);
CREATE INDEX idx_created_at ON campaigns (created_at);
CREATE INDEX idx_email_status ON campaigns (status, created_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM campaigns WHERE user_id = 1;
```

#### Asynchronous Processing
```python
from celery import Celery

celery_app = Celery('maily', broker='redis://localhost:6379/0')

@celery_app.task
def process_campaign_analytics(campaign_id: int):
    # Async processing of campaign analytics
    pass

@app.post("/campaigns/{campaign_id}/analyze")
async def analyze_campaign(campaign_id: int):
    process_campaign_analytics.delay(campaign_id)
    return {"status": "Analysis started"}
```

### Frontend Optimizations

#### Code Splitting
```typescript
// pages/index.tsx
import dynamic from 'next/dynamic';

const CanvasPanel = dynamic(() => import('../components/CanvasPanel'), {
  ssr: false,
  loading: () => <div>Loading canvas...</div>
});

const Chat = dynamic(() => import('../components/Chat'), {
  loading: () => <div>Loading chat...</div>
});
```

#### Component Memoization
```typescript
// components/ChatMessage.tsx
import React, { memo, useCallback } from 'react';

const ChatMessage = memo(({ message }) => {
  return <div className="message">{message.text}</div>;
});

const Chat = () => {
  const handleSend = useCallback((message: string) => {
    // Send message logic
  }, []);

  return (
    <div className="chat">
      {messages.map(msg => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
    </div>
  );
};
```

#### Web Workers for Heavy Computations
```typescript
// workers/canvas.worker.ts
self.onmessage = (e: MessageEvent) => {
  const { data } = e;
  // Process canvas operations
  const result = processCanvasData(data);
  self.postMessage(result);
};

// components/CanvasPanel.tsx
useEffect(() => {
  const worker = new Worker('/workers/canvas.worker.js');
  
  worker.onmessage = (e: MessageEvent) => {
    updateCanvas(e.data);
  };

  return () => worker.terminate();
}, []);
```

#### Image Optimization
```typescript
import Image from 'next/image';

const EmailTemplate = () => {
  return (
    <Image
      src="/templates/default.png"
      alt="Email Template"
      width={600}
      height={800}
      priority
      quality={75}
    />
  );
};
```

### Performance Monitoring

#### Backend Metrics
```python
from prometheus_client import Counter, Histogram
from fastapi import FastAPI

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

app = FastAPI()

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response
```

#### Frontend Metrics
```typescript
// utils/performance.ts
export const measurePerformance = (metric: string) => {
  if (typeof window !== 'undefined') {
    const navigation = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint');
    
    console.log(`${metric}:`, {
      loadTime: navigation.loadEventEnd - navigation.startTime,
      firstPaint: paint[0]?.startTime,
      firstContentfulPaint: paint[1]?.startTime,
    });
  }
};
```

### Optimization Tools

1. **Backend Profiling**
```bash
# Profile Python code
python -m cProfile -o output.prof main.py

# Analyze with snakeviz
snakeviz output.prof
```

2. **Frontend Analysis**
```bash
# Run Lighthouse audit
npx lighthouse http://localhost:3000 --view

# Analyze bundle size
npx next build && npx next analyze
```

3. **Database Optimization**
```bash
# Analyze slow queries
tail -f /var/log/postgresql/postgresql-slow.log

# Vacuum and analyze
VACUUM ANALYZE campaigns;
```

### Performance Testing

1. **Load Testing**
```bash
# Using k6 for load testing
k6 run load-test.js
```

2. **End-to-End Performance**
```bash
# Using Cypress for performance testing
npx cypress run --config video=true
```

## Deployment

### Cloud Providers

1. **AWS**
   - ECS for container orchestration
   - RDS for PostgreSQL
   - ElastiCache for Redis
   - Route53 for DNS

2. **Google Cloud**
   - GKE for Kubernetes
   - Cloud SQL for PostgreSQL
   - Memorystore for Redis
   - Cloud DNS

3. **Azure**
   - AKS for Kubernetes
   - Azure Database for PostgreSQL
   - Azure Cache for Redis
   - Azure DNS

### CI/CD Pipeline
```yaml
# Example GitHub Actions workflow
name: CI/CD
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          # Add deployment steps
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)

## Support

For support, please open an issue in the repository or contact the maintainers.

