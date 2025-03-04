# Maily Development Guide

## Build Commands
```bash
npm run build         # Build all packages (Turbo)
npm run build:web     # Build web app specifically
npm run dev           # Run development server
npm run start:web     # Start web app in production mode
```

## Test Commands
```bash
npm run test          # Run all tests
npm test -- -t "test name" # Run specific JS test 
npm test -- --watch   # Run tests in watch mode
pytest tests/unit/test_file.py::test_function -v  # Run specific Python test
pytest -xvs -m unit tests/  # Run all unit tests
pytest --cov=. --cov-report=html tests/  # Run tests with coverage
npm run test:e2e      # Run E2E tests
npm run test:smoke    # Run smoke tests
npm run test:verify   # Verify deployment
```

## Lint & Format Commands
```bash
npm run lint          # Run ESLint on all packages
npm run format        # Run Prettier on all files
```

## Code Style Guidelines
- **TypeScript**: Strict mode, avoid 'any', PascalCase for components/types, camelCase for variables
- **Python**: Type annotations required, single responsibility, clean architecture with DI
- **Formatting**: 2 spaces, 100 char line limit, single quotes, trailing commas
- **Imports**: Use path aliases (@/* for imports), organize imports (isort for Python)
- **Components**: Functional components with React hooks, small and focused
- **Error Handling**: ErrorBoundary for React, custom MailyError hierarchy in Python
- **Git Commits**: Follow conventional commits format (feat/fix/docs/chore/test)
- **Node/NPM**: Requires Node ≥20.11.1, NPM ≥8.0.0
- **Testing**: Use appropriate markers (unit/integration/e2e), mock external dependencies
- **Python Testing**: Use pytest fixtures, parametrize for multiple test cases
- **Convention**: Follow existing patterns from neighboring files when adding new code