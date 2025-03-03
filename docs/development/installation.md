# Installation Guide

This guide provides step-by-step instructions for setting up the Maily development environment on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 20.11.1 or later
- **Python**: Version 3.9 or later
- **Docker**: Latest stable version
- **Docker Compose**: Latest stable version
- **Git**: Latest stable version

## Clone the Repository

```bash
git clone https://github.com/yourusername/maily.git
cd maily
```

## Setting Up Node.js Environment

1. Install Node.js dependencies:

```bash
npm install
```

2. Set up environment variables:

```bash
cp .env.example .env
```

3. Edit the `.env` file to configure your local environment.

## Setting Up Python Environment

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Setting Up Docker Services

1. Start the required Docker services:

```bash
docker-compose up -d db redis
```

2. Initialize the database:

```bash
cd apps/api
python -m scripts.init_db
```

## Running the Development Environment

### Start All Services

```bash
npm run dev
```

### Start Individual Services

#### Web Frontend

```bash
npm run dev --filter=web
```

#### API Backend

```bash
cd apps/api
python main.py
```

#### AI Service

```bash
cd apps/ai-service
python main.py
```

## Verify Installation

1. Open your browser and navigate to:
   - Web app: http://localhost:3000
   - API: http://localhost:8000/docs
   - AI Service: http://localhost:8080/api/mesh/health

2. Run tests to ensure everything is working:

```bash
npm run test
```

## Troubleshooting

### Common Issues

- **Port conflicts**: If you encounter port conflicts, check if other applications are using the same ports and adjust in your `.env` file.

- **Database connection issues**: Ensure your database is running and the connection parameters in `.env` are correct.

- **Node.js version issues**: Use nvm (Node Version Manager) to switch to the required Node.js version.

### Getting Help

If you encounter any issues not covered here, please:

1. Check the [FAQ](../glossary-and-faq.md)
2. Reach out to the development team
3. Create an issue in the GitHub repository