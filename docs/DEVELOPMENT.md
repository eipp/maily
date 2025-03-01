# Maily Development Guide

## Overview

Maily is an AI-driven email marketing platform that automates campaign creation, personalization, scheduling, and analytics via a chat-centric interface. The system supports multimodal inputs, dynamic personalization, autonomous campaign management across multiple email providers, visual canvas creation, and blockchain-based verification.

## Architecture

Maily's architecture is divided into four main layers:

- **Frontend Layer:** Next.js, Tailwind CSS, React components
- **Backend Layer:** Vercel Serverless Functions, Supabase, Redis, workflow orchestration (Temporal)
- **AI Layer:** OctoTools framework, AI model adapters (OpenAI, Anthropic, Google)
- **Trust Infrastructure:** Blockchain-based verification for email campaigns

The project implements **hexagonal architecture** (ports and adapters) throughout, with the most comprehensive implementation being in the AI service integrations.

## Getting Started

### Prerequisites

- Node.js (v18.x or later)
- pnpm (v9.x or later)
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/maily/maily.git
   cd maily
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local` with your local configuration.

4. Start development services:
   ```bash
   docker-compose up -d
   ```

5. Start the development server:
   ```bash
   pnpm dev
   ```

The application will be available at `http://localhost:3000`.

## Repository Structure

```
maily/
├── apps/                      # Application packages
│   ├── web/                   # Next.js frontend application
│   ├── api/                   # FastAPI backend service
│   └── workers/               # Background processing workers
├── packages/                  # Shared libraries and utilities
│   ├── ai/                    # AI service and model adapters
│   ├── ui/                    # Shared UI components
│   ├── config/                # Shared configuration
│   └── utils/                 # Common utility functions
├── infrastructure/            # Infrastructure as code
├── docs/                      # Documentation
└── .github/                   # GitHub configuration
```

## Core Technologies

- **Frontend**: Next.js 14+, React 18+, TypeScript, Tailwind CSS
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy ORM with PostgreSQL
- **AI Layer**: OctoTools for agent orchestration, adapter pattern for models
- **Email Providers**: Resend, SendGrid, and Mailgun support via adapter pattern
- **Infrastructure**: Docker, Kubernetes, Helm charts, Terraform

## Authentication

Maily supports two authentication methods:

1. **JWT Authentication**: For user-facing authentication
2. **API Key Authentication**: For programmatic access to the API

The authentication flow follows these steps:
1. Client sends request with auth credentials (JWT token or API key)
2. Authentication middleware intercepts and validates the request
3. After successful authentication, user information is attached to the request

## Development Guidelines

### Code Style

- All code must follow our ESLint configuration
- TypeScript is required for all new code
- Use the Prettier configuration for code formatting
- Follow the [conventional commits](https://www.conventionalcommits.org/) specification

### Testing Requirements

- Unit tests for all business logic
- Component tests for UI components
- Integration tests for API endpoints
- End-to-end tests for critical user flows

We use Vitest for unit and component testing, and Playwright for end-to-end testing.

### Pull Request Process

1. Fork the repository and create a feature branch from `main`
2. Make your changes and ensure tests pass
3. Update documentation as needed
4. Submit a pull request to the `main` branch
