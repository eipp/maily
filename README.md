# Maily Platform

Maily is an AI-powered email campaign platform with advanced features including AI mesh networking, cognitive canvas, and predictive analytics.

## 🚀 Features

- **AI Mesh Network**: Collaborative AI agents working together on complex tasks
- **Cognitive Canvas**: Interactive canvas with real-time collaboration and layer management
- **Email Campaign Management**: Create, send, and track email campaigns
- **Analytics Dashboard**: Real-time insights and performance metrics
- **Template Library**: Customizable email templates
- **Trust Verification**: Blockchain-based verification of email campaigns
- **Multi-platform Integration**: Connect with various marketing platforms
- **Service Mesh**: Istio-based service mesh with mutual TLS and traffic management

## 📋 Project Structure

The repository follows a standardized structure:

```
maily/
├── apps/                   # Application services
│   ├── ai-service/         # AI Mesh Network service
│   ├── api/                # Main API backend
│   ├── web/                # Web frontend (Next.js)
│   ├── email-service/      # Email delivery service
│   └── workers/            # Background task workers
├── packages/               # Shared packages
│   ├── database/           # Database utilities
│   ├── error-handling/     # Error handling utilities
│   ├── ui-components/      # UI components
│   └── utils/              # Shared utilities
├── config/                 # Centralized configuration
├── docker/                 # Docker configuration
└── kubernetes/             # Kubernetes configuration
```

For a complete overview of the repository structure, see [REPOSITORY-STRUCTURE.md](./REPOSITORY-STRUCTURE.md).

## 🔧 Development

### Prerequisites

- Node.js (v20.11.1+)
- Python 3.9+
- Docker and Docker Compose

### Setup

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env

# Start services with Docker Compose
docker-compose up
```

### Running Locally

```bash
# Start all services
npm run dev

# Start specific service
npm run dev --filter=web
```

### Testing

```bash
# Run all tests
npm run test

# Run specific tests
npm test -- -t "test name"

# Run Python tests
cd apps/api && pytest
```

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory and can be viewed using MkDocs:

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve
```

## 🧪 Code Style

The codebase follows standardized conventions:

- **TypeScript**: Strict mode, avoid 'any', PascalCase for components/types, camelCase for variables
- **Python**: Type annotations required, single responsibility, clean architecture with DI
- **Formatting**: 2 spaces, 100 char line limit, single quotes, trailing commas
- **Imports**: Use path aliases (@/* for imports), organize imports (isort for Python)
- **Error Handling**: Use standardized error handling from packages/error-handling

For complete code style guidelines, see [CLAUDE.md](./CLAUDE.md).

## 🏗️ Building and Deployment

### Building

```bash
# Build all packages
npm run build

# Build specific package
npm run build --filter=web
```

### Deployment

Deployment is handled through Kubernetes using a unified command-line tool with phased deployment capabilities and service mesh integration:

```bash
# Deploy to staging with service mesh
./mailyctl.py phased-deploy --env=staging

# Deploy to production
./mailyctl.py phased-deploy --env=production

# Deploy as canary with 10% traffic weight
./mailyctl.py phased-deploy --env=production --canary --canary-weight=10

# Deploy with custom service mesh version
./mailyctl.py phased-deploy --env=staging --version=1.2.0

# Verify service mesh configuration
./mailyctl.py verify-mesh --env=staging --component=api
```

The deployment includes:
- Automated service mesh configuration with Istio
- Mutual TLS for secure service communication
- Circuit breakers for resilience
- Retry policies and timeout configuration
- Observability dashboards for service mesh metrics

For detailed deployment instructions, see the [Production Deployment Guide](docs/production-deployment-guide.md) and [Helm Chart README](infrastructure/helm/maily/README.md).

## 🤝 Contributing

Please read our [Contributing Guide](.github/docs/CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the terms of the [MIT license](LICENSE).