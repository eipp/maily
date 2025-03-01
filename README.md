# Maily - AI-Driven Email Marketing Platform

Maily is a revolutionary autonomous email marketing platform that transforms traditional marketing workflows through AI agent orchestration, multimodal integration, intelligent contact discovery, and blockchain-verified trust. The platform empowers users to create hyper-personalized, multi-channel campaigns with minimal effort by automating the entire process from contact discovery to performance analysis and verification.

## Features

- **Autonomous Operation**: AI agents handle 90% of the marketing workflow without human intervention
- **Cross-Platform Integration**: Unified view and coordinated outreach across email, social, and messaging platforms
- **AI-Powered Personalization**: Dynamic content generation tailored to individual recipient characteristics
- **Intelligent Contact Discovery**: Automated building of high-quality contact lists matched to campaign objectives
- **Continuous Optimization**: Self-improving algorithms that learn from campaign performance
- **Blockchain Verification**: Trust certificates and transparent campaign verification
- **Visual Canvas Creation**: Hybrid conversational-visual interface for sophisticated design

## User Interface & Experience

Maily features a unique hybrid interface that combines the best of conversational and visual design paradigms:

- **Chat-Centric Interaction**: Natural language conversations with specialized AI assistants for campaign strategy, content creation, audience analysis, and technical support
- **Visual Canvas Creation**: Intuitive drag-and-drop interface for creating sophisticated email designs with AI assistance
- **Multi-Agent AI System**: Specialized AI agents with distinct personalities and capabilities, working together to accomplish complex marketing tasks
- **Cross-Platform Orchestration**: Unified interface for managing campaigns across email, social media, and messaging platforms
- **Blockchain-Based Trust Verification**: Transparent verification of campaign performance and delivery using blockchain technology

## Documentation

For detailed documentation, please see the [docs](./docs) directory:

- [Development Guide](./docs/DEVELOPMENT.md) - Getting started, installation, and contribution guidelines
- [Architecture](./docs/ARCHITECTURE.md) - Technical architecture and design patterns
- [API Reference](./docs/API.md) - RESTful API endpoints with request/response examples
- [AI Adapters](./docs/ai-adapters.md) - AI adapter pattern implementation

## Domains

Maily is accessible through the following domains:

- **justmaily.com** - Main landing page and marketing website
- **app.justmaily.com** - The Maily application interface
- **console.justmaily.com** - Developer console and API documentation
- **api.justmaily.com** - API endpoints (for programmatic access)
- **docs.justmaily.com** - Public documentation

## API Reference

Maily provides a comprehensive RESTful API for integrating with the platform:

- **Standardized Endpoints**: Consistent RESTful API design across all endpoints
- **Authentication Options**: Support for both JWT and API key authentication
- **Comprehensive Documentation**: Detailed API documentation with request/response examples
- **Client Libraries**: Official SDKs for JavaScript, Python, Ruby, and PHP
- **Webhooks**: Event-driven integration with webhook support

For complete API documentation, see the [API Reference](./docs/API.md) or visit [console.justmaily.com](https://console.justmaily.com).

## Security and Compliance

Maily implements a comprehensive security and compliance architecture to protect sensitive data and ensure regulatory compliance:

- **Security Scanning Pipeline**: Automated security scanning using Trivy, Snyk, OWASP ZAP, SonarQube
- **Secrets Management**: Centralized secrets management using HashiCorp Vault with Kubernetes integration
- **Compliance Automation**: Policy-based compliance enforcement using Open Policy Agent (OPA) and Kyverno
- **Authentication & Authorization**: Robust authentication and authorization mechanisms
- **Security Monitoring**: Comprehensive security event monitoring with Prometheus alerts
- **Blockchain Security**: Advanced security measures for blockchain operations and verification

## Monorepo Structure

This project follows a modern monorepo architecture using Turborepo for optimal development experience:

```
maily/
├── apps/                      # Application packages
│   ├── web/                   # Next.js frontend application (Pages Router)
│   ├── api/                   # FastAPI backend service
│   └── workers/               # Background processing workers
├── packages/                  # Shared libraries and utilities
│   ├── ai/                    # AI service and model adapters
│   ├── ui/                    # Shared UI components
│   ├── config/                # Shared configuration
│   ├── database/              # Database models and Prisma client (JS/TS)
│   ├── email-renderer/        # Email templating and rendering
│   ├── analytics/             # Analytics utilities
│   └── utils/                 # Common utility functions
├── infrastructure/            # Infrastructure as code
├── scripts/                   # Development and CI scripts
├── docs/                      # Documentation
├── tests/                     # E2E and integration tests
└── .github/                   # GitHub configuration
```

## Core Technologies

- **Frontend**: Next.js 14+, React 18+, TypeScript, Tailwind CSS
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM with PostgreSQL
- **AI Layer**: OctoTools for agent orchestration, adapter pattern for models
- **Email Providers**: Resend, SendGrid, and Mailgun support via adapter pattern
- **Infrastructure**: Docker, Kubernetes, Helm charts, Terraform
- **JavaScript Database**: Prisma with PostgreSQL
- **Trust Layer**: Solana-based blockchain verification for email campaigns
- **UI Components**: React Aria for accessible components, Radix UI for advanced components
- **Canvas**: tldraw with Yjs for real-time collaboration

## Development Philosophy

Maily is developed and maintained by a lean team consisting of a founder and an AI coding agent. This unique approach enables:

- **Rapid Development**: Leveraging AI capabilities for accelerated development cycles
- **Consistent Code Quality**: AI-enforced coding standards and patterns
- **Comprehensive Documentation**: Automated documentation generation and maintenance
- **Efficient Problem Solving**: AI-assisted debugging and optimization
- **Scalable Architecture**: Design patterns that facilitate growth without proportional team expansion

This lean development model allows Maily to deliver enterprise-grade features while maintaining the agility and innovation of a startup.

## Getting Started

See the [Development Guide](./docs/DEVELOPMENT.md#getting-started) for detailed instructions on setting up the development environment.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
