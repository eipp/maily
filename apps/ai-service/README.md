# AI Service

This directory contains the AI Service which powers the AI Mesh Network and other AI features in the Maily platform.

## Structure

- `models/` - Data models and schemas
- `routers/` - API endpoints and route handlers
- `services/` - Core business logic and service implementations
- `utils/` - Utility functions and helper modules

## Setup & Development

```bash
# Install dependencies
pip install -r requirements-ai-mesh.txt

# Run the service
python main.py

# Run tests
python run_tests.py
```

## Integration

The AI Service integrates with:
- Redis for caching and message passing
- Database for persistence
- LLM providers (Anthropic, OpenAI, etc.)

See [README-AI-MESH.md](./README-AI-MESH.md) for detailed information about the AI Mesh Network functionality.