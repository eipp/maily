# Maily - AI-Powered Email Campaign Platform

Maily is a modern email campaign platform that leverages AI to create, design, and optimize email campaigns. It combines multiple AI providers with advanced analytics and monitoring capabilities.

## Features

- 🤖 AI-powered content generation using multiple providers (OpenAI, Anthropic, Google, etc.)
- 📊 Real-time analytics and performance monitoring
- 🔒 Enterprise-grade security and rate limiting
- 💾 Efficient caching with Redis
- 📈 Distributed computing with Ray
- 🔍 Comprehensive logging and tracing
- 🧪 Extensive test coverage with automated CI/CD

## Tech Stack

### Backend
- FastAPI
- PostgreSQL
- Redis
- Ray (Distributed Computing)
- Prometheus & Grafana (Monitoring)
- Loguru (Logging)
- pytest (Testing)

### Frontend
- Next.js 14
- React
- Redux Toolkit
- TailwindCSS
- Winston (Logging)
- Jest & React Testing Library
- Cypress (E2E Testing)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### Backend Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Initialize database:
   ```bash
   # Ensure PostgreSQL is running
   psql -U postgres -c "CREATE DATABASE maily"
   ```

5. Run the backend:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd app
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

## Testing

### Backend Tests

```bash
cd backend
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Frontend Tests

```bash
cd app
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- CampaignForm.test.tsx
```

### E2E Tests

```bash
cd app
# Open Cypress Test Runner
npm run cypress:open

# Run Cypress tests headlessly
npm run cypress:run
```

## Project Structure

```
maily/
├── app/                # Next.js frontend application
│   ├── components/    # React components
│   ├── hooks/         # Custom React hooks
│   ├── utils/         # Utility functions
│   ├── services/      # API services
│   ├── __tests__/     # Frontend unit tests
│   └── cypress/       # E2E tests
├── backend/
│   ├── main.py        # FastAPI application
│   ├── ai/            # AI agents and services
│   ├── api/           # API endpoints
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── tests/         # Backend tests
├── docs/              # Project documentation
├── terraform/         # Infrastructure as Code
├── .github/           # GitHub Actions workflows
└── prometheus/        # Monitoring configuration
```

## CI/CD Pipeline

Our GitHub Actions workflow automatically:
1. Runs backend tests with pytest
2. Runs frontend unit tests with Jest
3. Runs E2E tests with Cypress
4. Generates and uploads test coverage reports
5. Builds and deploys the application

Coverage requirements:
- Overall project: 80%
- Backend: 85%
- Frontend: 75%
- New code changes: 80%

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Spec: http://localhost:8000/openapi.json

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests:
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd app
   npm test

   # E2E tests
   cd app
   npm run cypress:run
   ```
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Backend: Follow PEP 8 guidelines
- Frontend: Follow Prettier and ESLint configurations
- Use meaningful commit messages
- Write tests for new features

## Documentation

- Project documentation is built with MkDocs
- View the docs locally:
  ```bash
  pip install mkdocs
  mkdocs serve
  ```
- Documentation is available at: http://localhost:8000

## Monitoring

- Prometheus metrics: http://localhost:8000/metrics
- Grafana dashboards: http://localhost:3000/dashboards
- Log files:
  - Backend: `backend/logs/`
  - Frontend: `app/logs/`

## Disaster Recovery

For disaster recovery procedures and guidelines, see [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md).

## Architecture

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the [documentation](http://localhost:8000)
2. Open an issue
3. Contact the maintainers

