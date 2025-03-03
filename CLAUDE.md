# Maily Development Guide

## Build Commands
```bash
npm run build         # Build all packages (Turbo)
npm run build:web     # Build web app specifically
npm run dev           # Run development server
```

## Test Commands
```bash
npm run test          # Run all tests
npm test -- -t "test name" # Run specific JS test
npm test -- --watch   # Run tests in watch mode
pytest tests/unit/test_file.py::test_function -v  # Run specific Python test
pytest --cov=. --cov-report=html tests/  # Run tests with coverage
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
- **Logging**: No console.log (only warn/error allowed)
- **Tests**: Place tests in proper directories or use descriptive naming conventions
- **Convention**: Follow existing patterns from neighboring files when adding new code