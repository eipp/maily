# Maily Development Guide

## Build Commands
```bash
npm run build         # Build all packages (Turbo)
npm run build:web     # Build web app specifically
npm run dev           # Run development server
npm run start:web     # Start web app in production mode
npm run start:email   # Start email service in production mode
npm run clean         # Clean build artifacts
```

## Test Commands
```bash
npm run test          # Run all tests
npm test -- -t "test name" # Run specific JS test 
npm test -- --watch   # Run tests in watch mode
npm test -- --coverage # Run tests with coverage reports
pytest tests/unit/test_file.py::test_function -v  # Run specific Python test
pytest -xvs -m unit tests/  # Run all unit tests
pytest --cov=. --cov-report=html tests/  # Run tests with coverage
npm run test:e2e      # Run E2E tests
npm run test:e2e:staging # Run E2E tests against staging
```

## Lint & Type Check Commands
```bash
npm run lint          # Run ESLint on all packages
npm run format        # Run Prettier on all files
npx tsc --noEmit     # Run TypeScript type checking
python -m black .     # Format Python code
python -m isort .     # Sort Python imports
python -m mypy .      # Python type checking
python -m flake8 .    # Python linter
```

## Code Style Guidelines
- **TypeScript**: Strict mode, avoid 'any', PascalCase for components/types, camelCase for variables
- **Python**: Type annotations required, single responsibility, clean architecture with DI
- **Formatting**: 2 spaces, 100 char line limit, single quotes, trailing commas
- **Imports**: Use path aliases (@/* for imports), organize imports with isort
- **Components**: Functional components with React hooks, small and focused
- **Error Handling**: Use standardized error classes from packages/error-handling
- **Git Commits**: Follow conventional commits format (feat/fix/docs/chore/test)
- **Testing**: Use appropriate markers (unit/integration/e2e), mock external dependencies
- **Convention**: Follow existing patterns from neighboring files when adding new code

## Error Handling
- Use appropriate error classes: `ApplicationError` (TS/JS) or `MailyError` subclasses (Python)
- Include error codes, status codes, and detailed messages
- React components: Wrap with `ErrorBoundary` from `packages/error-handling/src/react`
- FastAPI: Use error middleware from `packages/error_handling/python/middleware`
- Map external service errors to internal error types using `handleHttpError` (TS) or appropriate mappers (Python)
- Maintain consistent error response format with trace IDs
- JavaScript: `import { ValidationError, NotFoundError } from '@maily/error-handling';`
- Python: `from packages.error_handling.python.errors import ValidationError, NotFoundError`

## Standardized Libraries
- **HTTP Client**: Use the standardized HTTP client from `packages/error-handling/python/http_client`
  ```python
  from packages.error_handling.python.http_client import get, post, HttpClient
  
  # Using convenience functions
  response = await get("https://api.example.com/data", params={"limit": 10})
  data = response.json()
  
  # Or create a client with a base URL
  client = HttpClient(base_url="https://api.example.com")
  response = await client.async_get("/data", params={"limit": 10})
  ```
- **Testing**: Use Vitest for JavaScript/TypeScript tests (Jest is deprecated)
- **Redis**: Import from `packages/database/src/redis`
  ```python
  from packages.database.src.redis import redis_client, get, set, delete
  
  # Using the client
  await redis_client.set("key", "value")
  value = await redis_client.get("key")
  ```
- **GraphQL**: Use Apollo Client for GraphQL in JavaScript/TypeScript
- **Telemetry**: Use OpenTelemetry packages from `packages/config/monitoring`

## Deprecated Modules
- `apps/api/cache/redis.py` - Use `packages/database/src/redis/redis_client.py` instead
- `apps/api/cache/redis_service.py` - Use implementations based on standardized client
- `apps/web/jest.config.js` - Use Vitest instead
- HTTP Libraries: `requests`, `aiohttp`, `urllib3` - Use `httpx` instead