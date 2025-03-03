# Local Development Guide

This guide provides instructions for setting up and running the Maily platform locally for development.

## Prerequisites

- Node.js (v20.11.1 or later)
- Python 3.9+
- Docker and Docker Compose
- Git

## Initial Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/maily.git
cd maily
```

2. Install dependencies:

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your local configuration
```

## Running Services

### Running the Full Stack

To run all services together:

```bash
npm run dev
```

This will start all services defined in the Turborepo configuration.

### Running Individual Services

To run specific services:

```bash
# Run the web application
npm run dev --filter=web

# Run the API service
cd apps/api
python main.py

# Run the AI service
cd apps/ai-service
python main.py
```

## Database Setup

1. Start the database:

```bash
docker-compose up -d db
```

2. Run migrations:

```bash
cd apps/api
python -m scripts.run_migrations
```

## Testing

### Running Tests

```bash
# Run all tests
npm run test

# Run tests for a specific package
npm run test --filter=web

# Run Python tests
cd apps/api
pytest
```

### Running Linting and Type Checking

```bash
# Run ESLint
npm run lint

# Run TypeScript type checking
npm run typecheck

# Run Python type checking
mypy apps/api
```

## Working with the AI Mesh Network

The AI Mesh Network requires additional setup:

1. Set up required environment variables for AI service:

```bash
# Add these to your .env file
AI_SERVICE_API_KEY=your_api_key
ANTHROPIC_API_KEY=your_anthropic_key
```

2. Start Redis (required for AI service):

```bash
docker-compose up -d redis
```

3. Run the AI service:

```bash
cd apps/ai-service
python main.py
```

## Development Workflow

1. Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and test them locally

3. Run formatting:

```bash
npm run format
```

4. Run tests:

```bash
npm run test
```

5. Commit your changes using conventional commits format

6. Push your branch and create a pull request

## Troubleshooting

### Common Issues

- **Port conflicts**: Services use default ports that might conflict with existing services on your machine. Check the error messages for port conflicts and adjust as needed.

- **Database connection issues**: Ensure your database is running and the connection details in your `.env` file are correct.

- **Redis connection issues**: AI service requires Redis. Ensure Redis is running if you're working with AI features.

### Getting Help

If you encounter any issues, check the [FAQ](../glossary-and-faq.md) or reach out to the development team.