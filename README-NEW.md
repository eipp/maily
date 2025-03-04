# Maily Platform

Maily is an AI-powered email campaign platform with advanced features including AI mesh networking, cognitive canvas, and predictive analytics.

## 🚀 Features

- **AI Mesh Network**: Collaborative AI agents working together on complex tasks
- **Email Campaign Management**: Create, send, and track email campaigns
- **Analytics Dashboard**: Real-time insights and performance metrics
- **Template Library**: Customizable email templates
- **Trust Verification**: Blockchain-based verification of email campaigns
- **Multi-platform Integration**: Connect with various marketing platforms

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

Deployment is handled through Kubernetes:

```bash
# Deploy to staging
scripts/deploy/staging.sh

# Deploy to production
scripts/deploy/production.sh
```

For detailed deployment instructions, see the [Production Deployment Guide](docs/production-deployment-guide.md).

## 🤝 Contributing

Please read our [Contributing Guide](.github/docs/CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the terms of the [MIT license](LICENSE).