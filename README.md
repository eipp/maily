# Maily

Maily is an AI-powered email campaign platform with advanced features including AI mesh networking, cognitive canvas, and predictive analytics.

## 🚀 Features

- **AI Mesh Network**: Collaborative AI agents working together on complex tasks
- **Email Campaign Management**: Create, send, and track email campaigns
- **Analytics Dashboard**: Real-time insights and performance metrics
- **Template Library**: Customizable email templates
- **Trust Verification**: Blockchain-based verification of email campaigns
- **Multi-platform Integration**: Connect with various marketing platforms

## 📋 Project Structure

```
maily/
├── apps/                   # Application services
│   ├── ai-service/         # AI Mesh Network service
│   ├── api/                # Main API backend
│   ├── web/                # Web frontend (Next.js)
│   ├── email-service/      # Email delivery service
│   ├── analytics-service/  # Analytics processing
│   ├── campaign-service/   # Campaign management
│   └── workers/            # Background task workers
├── packages/               # Shared packages
│   ├── ui/                 # UI components
│   ├── utils/              # Shared utilities
│   ├── config/             # Configuration
│   ├── domain/             # Shared domain models
│   ├── testing/            # Testing utilities
│   └── config-schema/      # Configuration schema
├── docker/                 # Docker configuration
├── infrastructure/         # Infrastructure as code
├── kubernetes/             # Kubernetes configuration
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

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
```

### Running locally

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

Or visit our [documentation site](https://docs.maily.com).

## 🤝 Contributing

Please read our [Contributing Guide](.github/docs/CONTRIBUTING.md) to get started.

## 📄 License

This project is licensed under the terms of the [MIT license](LICENSE).

## 🔗 Links

- [Production Deployment Guide](docs/production-deployment-guide.md)
- [API Documentation](docs/api/overview.md)
- [Architecture Overview](docs/internal/architecture-overview.md)# Repository Organization Improvements

The repository has been thoroughly reorganized following state-of-the-art practices. All details can be found in [REPO-IMPROVEMENTS.md](REPO-IMPROVEMENTS.md)
